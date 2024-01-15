# Running the FastAPI-React app:
Note - I am using a VM on my machine with an IP address of 192.168.1.30. You may need to change this.

Create 2 terminals:
1. FastAPI backend terminal
2. ReactJS frontend terminal

## 1. Start backend server:

### First install all required modules:
```shell
cd backend
python -m pip install -r requirements.txt
```

### Run the server:
`uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
Starts the server on: http://192.168.1.30:8000/

## 2. Start frontend server:

### First install all required modules:
```shell
cd backend
npm install
```

### Run the server:
`HOST=0.0.0.0 npm start`
Starts the server on: http://192.168.1.30:3000/

## CORS errors:
To remove Cross Origin Resource Sharing errors - I added a section in `backend/app/main.py`:
You may need to add your IP address here until we can figure out a better solution.

```python 
origins = [
    "http://192.168.1.30:3000",
    "https://192.168.1.30:3000",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```