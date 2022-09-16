# python-mgjson
A nifty library for encoding mgjson documents from python.

Made possibly by the the works of [JuanIrache](https://github.com/JuanIrache/mgjson) . This library is a new partial implementation in python for generating Motion Graphics Json documents.

Static data properties of type int, boolean and ascii-string are supported.
Dynamic data as time series are supported. These will be translated to timezone encoded time series.

## installation

```python
pip install mgjson
```

## Usage

```python
from mgjson import MgJSON

mgjson = MgJSON()

# static properties
mgjson.add_property("numberOfCats", 3)
mgjson.add_property("isItTrue", False)
mgjson.add_property("title", "A new adventure awaits!")

# dynamic data (time series)
mgjson.add_stream("temperature", [[0.0, 1.000], [2.59292, 0.777]])

print(mgjson.json)
```



## License

MIT
