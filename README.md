Install pulp:
```
python3 -m pip install pulp
```

Run type checker:
```
pyright
```

Run autoformatter:
```
black .
```

Remove unused imports:
```
autoflake --remove-all-unused-imports --ignore-pass-statements -i src/**/*
```

Run code:
```
python3 optimeyes.py
```

Build standalone app:
```
python3 setup.py py2app
```

Links:

- [Pulp documentation](https://coin-or.github.io/pulp/index.html)
- [Pulp source](https://github.com/coin-or/pulp/blob/master/pulp/pulp.py)
