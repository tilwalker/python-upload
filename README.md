# python-upload

## Install packages
```
pip install -r requirements.txt 
```

## Start project
```
python3 app.py
```

## Docker start

### Build container
```
docker build --tag python-img
```
```
docker run -d -p 5000:5000 python-img
```

app running in url: http://localhost:5000