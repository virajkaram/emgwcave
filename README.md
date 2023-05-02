# emgwcave
A python module to vet EMGW candidates

Install - 
1. Clone this repo
2. `pip install -e .`

Usage -
To use this module, you must first configure the kowalski connection details in your 
environment. This can be done by setting the following environment variables:
1. export KOWALSKI_TOKEN=your_kowalski_token
2. export KOWALSKI_URL=your_kowalski_url
3. export KOWALSKI_PORT=your_kowalski_port

Then, you can use the module as follows :
```
python -m emgwcave <skymappath> <cumulative probability> <output_directory> 
```

By default, the start date will be read from the skymap.

You can list other options using : 
```
python -m emgwcave --help
```
