from fastapi import FastAPI, HTTPException #Import FastAPI
from pydantic import BaseModel #to create POST objects
from fastapi import UploadFile #to handle file uploads in POST requests
from input_campaign_data import load_and_clean
from efficiency_analysis import load_cleaned, compute_efficiency
from funnel_analysis import compute_funnel
from analyze_campaign import main
from pathlib import Path

app = FastAPI() #Create an app instance of FastAPI. 
#This is the main entry point for defining API routes and handling requests. 
#The app variable will be used to register path operations (API endpoints) using decorators like @app.get() and @app.post().

#HTTP protocol is how browser interacts with the server 
#other protocols: web socket, telnet, webrtc 
#HTTP methods: GET, POST (body w the request), PUT (update operations), DELETE 
# Build a POST API that takes Path filename as a parameter with POST method 

######################################################################
@app.get("/cleaned_data_local_test") #Write a path operation decorator like @app.get("/"). GET is the operator, "/" is the path
#APIs are defined behind certain routes e.g., /cleaned_data_test is a route. 
#API server on the laptop is a process, which is always kept active by OS
async def root(): #Define a path operation function
    df = load_and_clean(path = Path("campaign_data_week1.csv"))
    return df.head().to_dict()

@app.get("/cleaned_data_from_file")
async def get_cleaned_data_from_file(file_path: str):  # Query parameter from URL
    path = Path(file_path)
    #Two validations are added: 
    #(1) File existence check — returns a 404 if the path doesn't point to a real file
    #(2)Extension check — returns a 400 if the file isn't a .csv
    # Both raise HTTPException which FastAPI automatically converts into proper JSON error responses
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    if path.suffix != ".csv":
        raise HTTPException(status_code=400, detail="Only .csv files are supported")
    
    df = load_and_clean(path=path)
    return df.head().to_dict()

#################################################################################

@app.get("/efficiency_analysis_local_test") 
async def efficiency_analysis_test(): 
    input_df = load_cleaned(path = Path("cleaned_campaign.csv"))
    df = compute_efficiency(input_df,shipping_cost=0, product_cost_pct=0)
    return df.head().to_dict()

@app.get("/efficiency_analysis_from_file") 
async def efficiency_analysis_from_file(file_path: str):
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    if path.suffix != ".csv":
        raise HTTPException(status_code=400, detail="Only .csv files are supported")

    input_df = load_cleaned(path=path)
    df = compute_efficiency(input_df, shipping_cost=0, product_cost_pct=0)
    return df.head().to_dict()

class InputFile(BaseModel): #class name defined in Pascal case
    filePath: str #Javascript style or JSON variable name defined in camel case

@app.post("/efficiency_analysis_from_file") 
async def efficiency_analysis_from_file(input_file_path: InputFile): #Function name defined in Python in snake case
    path = Path(input_file_path.filePath) 
    #input_file_path is an object = an instance of InputFile, which has a filePath attribute. This allows us to access the file path sent in the POST request body.
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {input_file_path.filePath}")
    if path.suffix != ".csv":
        raise HTTPException(status_code=400, detail="Only .csv files are supported")

    input_df = load_cleaned(path=path)
    df = compute_efficiency(input_df, shipping_cost=0, product_cost_pct=0)
    return df.head().to_dict()

@app.post("/efficiency_analysis_from_upload_file")
async def efficiency_analysis_from_upload_file(file: UploadFile):
    input_df = load_cleaned(file.file) #file.file is a file-like object that can be passed directly to our existing loading/cleaning function, which expects a file path or file-like object.
    df = compute_efficiency(input_df, shipping_cost=0, product_cost_pct=0)
    return df.head().to_dict()
    #return {"Uploaded file name": file.filename}
    #This endpoint accepts a file upload via POST request and simply returns the filename in the response.

############################################################################

@app.post("/funnel_analysis_from_upload_file")
async def funnel_analysis_from_upload_file(file: UploadFile):
    input_df = load_cleaned(file.file) #file.file is a file-like object that can be passed directly to our existing loading/cleaning function, which expects a file path or file-like object.
    df = compute_funnel(input_df)
    return df.head().to_dict()

############################################################################

@app.post("/analyze_campaign") 
async def analyze_campaign(file: UploadFile):
    main(argv: list[str] | None = None)
    return {"message": "Hello Big World"}