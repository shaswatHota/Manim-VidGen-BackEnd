# Architecture plans

## 3 stage architecture :

I have 2 ideas regarding the flow of prompt and enhancement of prompt both require an intermediate stage before the code writing and after the scene planning stage 
It is a contractor stage which will enforce strict rules for the llm beforce code generation .It will improve accouracy decently.

**Architecture 1:** Extra LLM call as intermediate stage
The contractor stage will be an llm call which  will only write contract regarding the scenes . For each scenes the contract will be in JSON format which will specify which base_class Literal it is using . Basically it will have all the informations regarding how is each scene mapped with all the other scenes .
    use cases : 
    1. Complex animation sequencing that requires API-level decisions (Transform vs ReplacementTransform vs TransformMatchingShapes)
    2. 3D scene detection (ThreeDScene vs MovingCameraScene)
    3. Performance hints like "this has 8+ objects, avoid animating all at once"
**Architecture 2:** Functional validation with keyword matching 
The contractor stage will be a function call , in this function we will maintain a keyword list . It will map with the scene plan and decide the structure and which base_class will be used and return the output in clean JSON format which will be passed to the next stage along with the stage a plan of the scene to generate the code .


## AST TREE implementation
we will have a validation layer before running the generated code on our server .First we will generate the AST tree of the code and do a basic keyword match to check if it has wrote potential dangerous calls like 

```python
    FORBIDDEN_CALLS = {
    # code execution
    "eval", "exec", "compile",
    "__import__",
    
    # file system
    "open", "read", "write",
    "os.remove", "os.unlink",
    "os.rmdir", "shutil.rmtree",
    
    # shell / process
    "os.system", "os.popen",
    "subprocess.run", "subprocess.call",
    "subprocess.Popen", "subprocess.check_output",
    
    # network
    "socket", "urllib", "requests",
    "http.client", "ftplib",
    
    # serialization (unsafe loaders)
    "pickle.loads", "pickle.load",
    "yaml.load",          # safe variant is yaml.safe_load
    "marshal.loads",
    
    # dynamic attribute access with variables
    "getattr", "setattr", "delattr",
    
    # introspection escape hatches
    "__class__", "__bases__", "__subclasses__",
    "__globals__", "__builtins__",
    "__code__", "__closure__",
    
    # interactive / debug
    "input", "breakpoint",
    "pdb", "ipdb",
    
    # environment
    "os.environ", "os.getenv",
    }

    FORBIDDEN_IMPORTS = {
        "os", "sys", "subprocess",
        "socket", "requests", "urllib",
        "pickle", "marshal", "shelve",
        "importlib", "ctypes", "cffi",
        "tempfile", "shutil",
        "threading", "multiprocessing",
        "signal", "atexit",
    }
```
## Retry Logic
If a match is found in the AST validation or an error occur during execution of the program it will retry the program with the error message appended to the next prompt . There will be finite number of retries after which it will grace fully stop the retry with an error message or suggestion to avoid infinite retries .