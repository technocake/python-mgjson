"""mgjson parsing, formating and serializing."""
import json
import datetime

ALLOWED_STATIC_DATATYPES = [int, bool, str]

DATATYPES_MAP = {
    int: "number",
    bool: "boolean",
    str: "string"
}


class MgJSON():
    """MgJSON partially implemented according to mgjson schema 2.0."""

    def __init__(self):
        """Initialize a mgjson document.

        Data is added by methods: add_property and add_stream.
        """
        self.outlines = []
        self.streams = []

    @property
    def json(self):
        """Serialize to json."""
        doc = create_doc(dynamic=len(self.streams) > 0)

        for outline in self.outlines:
            doc["dataOutline"].append(outline)

        for stream in self.streams:
            doc["dataDynamicSamples"].append(stream)

        return json.dumps(doc, default=vars, indent=4)

    def add_property(self, name, value, display_name=None):
        """Add static property to be encoded to the mgjson doc.

        Can be either ascii-string, boolean or number.
        Static mgjson data are put in the data outline part of the document.
        """
        if type(value) == int:
            encoder = StaticMGJsonNumber

        elif type(value) == str:
            encoder = StaticMGJsonString

        else:
            encoder = StaticMGJsonData

        self.outlines.append(encoder(name, value, display_name))

    def add_stream(self, name, stream, display_name=None, interpolation=None):
        """
        Encode a stream of timestamped numbers.

        Input format:
            [{0.00, 23.0001124}]
        Output format:
            bloaty. See  https://json-schema.app/view/%23/%23%2Fdefinitions%2FdataDynamicSampleSet?url=https%3A%2F%2Fraw.githubusercontent.com%2FJuanIrache%2Fmgjson%2Fmaster%2FMGJSON_Schema2.0.0.json       # noqa

        Dynamic data are described in the data outline part of the document.
        The actual data series is put in DynamicSamples part.
        """
        if True:  # TODO: detect type of data stream values.
            encoder = DynamicMgJSONData
        else:
            # TODO: support more kinds of datatype streams
            encoder = DynamicMgJSONData

        stream = encoder(name, stream, display_name, interpolation)

        self.outlines.append(stream.outline)
        self.streams.append(stream.data)


class StaticMGJsonData:
    """Static mgjson data."""

    matchName = None
    displayName = None
    dataType = None
    value = None

    def __init__(self, name, value, display_name=None):
        """Encode a static property of type deducted from value.

        Can be either string, boolean or number.
        See: https://json-schema.app/view/%23/%23%2Fdefinitions%2FdataGroup/%23%2Fdefinitions%2FdataStatic?url=https%3A%2F%2Fraw.githubusercontent.com%2FJuanIrache%2Fmgjson%2Fmaster%2FMGJSON_Schema2.0.0.json  # noqa
        """
        data_type = type(value)
        if data_type not in ALLOWED_STATIC_DATATYPES:
            raise(f"Unsupported datatype, must be one of {ALLOWED_STATIC_DATATYPES}")  # noqa

        if display_name is None:
            display_name = name.capitalize()

        self.objectType = "dataStatic"
        self.displayName = display_name
        self.dataType = dict(type=DATATYPES_MAP[data_type])
        self.matchName = name
        self.value = value


class StaticMGJsonNumber(StaticMGJsonData):
    """Encoding a number. How hard can it be."""

    def __init__(self, name, value: int, display_name=None):
        """Load a number and describe a ton of redudant information.

        All according to schema 2.0.

        mgjson expects us to describe the number of digits and decimals.
        Input value is forced to be int and thus we can count the number
        of digits in a naive way.
        """
        super().__init__(name, value, display_name)

        self.dataType["numberStringProperties"] = {
            "pattern": {
                "isSigned": True,
                "digitsInteger": len(str(value)),
                "digitsDecimal": 0
            },
            "range": dict(
                occuring=dict(min=value, max=value),
                legal=dict(min=-2147483648, max=2147483648)
            ),
        }


class StaticMGJsonString(StaticMGJsonData):
    """Encoding a string. How hard can it be."""

    def __init__(self, name, value: int, display_name=None):
        """Load a ascii string and create mgjson data outline.

        All according to schema 2.0.
        mgjson expects us to describe the length of the string.
        """
        super().__init__(name, value, display_name)

        self.dataType["paddedStringProperties"] = {
            "maxLen": len(value),
            "maxDigitsInStrLength": 2,
            "eventMarkerB": False
        }


class DynamicMgJSONData:
    """Class for encoding dynamic stream data to mgjson format.

    mgjson structure is divided into two main parts for dynamic data.
    Data Outline and the set of data itself (DynamicSamples).
    """

    outline = None
    data = None
    interpolation = "hold"  # or linear

    def __init__(self, name, stream, display_name=None, interpolation=None):
        """Load with a list of data (stream).

        The stream is a list of datapoints - [time, value].
        time := float
            the number of seconds from origin. (0.0)
        value := float
            Data value at that point in time.

        The streams data outline is first created, describing the datatype.
        Then the sample set is encoded and prepared.
        """
        if display_name is None:
            display_name = name.capitalize()

        if not interpolation:
            interpolation = self.interpolation

        maxval = max(stream, key=lambda elem: elem[1])[1]
        minval = min(stream, key=lambda elem: elem[1])[1]
        count = len(stream)
        data = []

        self.outline = {
            "objectType": "dataDynamic",
            "displayName": display_name,
            "sampleSetID": name,
            "dataType": {
                "type": "numberString",
                "numberStringProperties": {
                    "pattern": {
                        "digitsInteger": 3,
                        "digitsDecimal": 15,
                        "isSigned": True
                    },
                    "range": {
                        "occuring": {
                            "min": minval,
                            "max": maxval
                        },
                        "legal": {
                            "min": -2147483648,
                            "max": 2147483648
                        }
                    }
                },
                "paddedStringProperties": {
                    "maxLen": 0,
                    "maxDigitsInStrLength": 0,
                    "eventMarkerB": False
                }
            },
            "interpolation": interpolation,
            "hasExpectedFrequecyB": False,
            "sampleCount": count,
            "matchName": name
        }

        for time, value in stream:
            data.append(
                dict(
                    time=timestamp(time),
                    value=encode_number(value)
                )
            )

        self.data = {
            "sampleSetID": name,
            "samples": data
        }


def create_doc(dynamic=True):
    """Make the mgjson document. Ready to later be filled with data."""
    if dynamic:
        return {
            "version": "MGJSON2.0.0",
            "creator": "python",
            "dynamicSamplesPresentB": True,
            "dynamicDataInfo": {
                "useTimecodeB": False,
                "utcInfo": {
                    "precisionLength": 3,
                    "isGMT": True
                }
            },
            "dataOutline": [],
            "dataDynamicSamples": [],
        }
    else:
        return {
            "version": "MGJSON2.0.0",
            "creator": "python",
            "dynamicSamplesPresentB": False,
            "dataOutline": [],
        }


def timestamp(seconds):
    """Relative time point to unix time (from 1970-1-1)."""
    delta = datetime.timedelta(seconds=seconds)
    dt = datetime.datetime(1970, 1, 1) + delta
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def encode_number(number):
    """Encode a number to mgjson supported numberstring format.

    mgjson expects a string encoded number prefixed with +/-
    """
    return f"{number:+020.15f}"


if __name__ == '__main__':
    # Tests placeholder:
    mgjson = MgJSON()

    # static properties
    mgjson.add_property("numberOfCats", 3)
    mgjson.add_property("isItTrue", False)
    mgjson.add_property("title", "A new adventure awaits!")

    # dynamic data (time series)
    mgjson.add_stream("temperature", [[0.0, 1.000], [2.23, 0.777]])

    print(mgjson.json)
