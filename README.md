# emgwcave
A python module to vet EMGW candidates

Install - 
1. Clone this repo
2. `pip install -e .`
3. Clone and similarly install the latest release of the penquins repo in your environment - https://github.com/dmitryduev/penquins

Usage -
To use this module, you must first configure the kowalski connection details in your 
environment. This can be done by setting the following environment variables:
1. export KOWALSKI_TOKEN=your_kowalski_token
2. export KOWALSKI_URL=your_kowalski_url
3. export KOWALSKI_PORT=your_kowalski_port

Then, you can use the module as follows :
```
python -m emgwcave -s <skymappath> -p <cumulative probability> -end <end_date> 
-out <output_directory>
```

By default, the start date will be read from the skymap.

You can list other options using : 
```
python -m emgwcave --help
```
