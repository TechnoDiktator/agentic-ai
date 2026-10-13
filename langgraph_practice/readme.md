
conda create -n langgraph-test  python=3.11 -y

conda activate langgraph-test

python -m pip install ipykernel

pip install -r requirements.txt

<!-- Register Kernel -->
<!-- python -m ipykernel install --user --name langgraph-test --display-name "Python (langgraph-test) -->