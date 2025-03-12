## Project Setup

1. Clone this repository and run ```cd scraping-server```
2. Install dependecies with ```pip install -r requirements.txt```
3. run ```cd scripts/models/my-llama3/```
4. run ```ollama create my-llama3 -f ./Modelfile```
5. from root directory run ```python3 app.py```


## Pre-requisites

1. Ollama installed and served.
2. llama3:8b-instruct-fp16 installed
3. RTX 4090


if the system have a smaller gpu, you can install smaller model from ollama and replace the model name in scripts/models/my-llama3/Modelfile
