# gpt_decorator

Example usage:

```
(venv) conor@zoroaster gpt_decorator % python main.py
> [0/8192] greet me please. my name is conor.
Hello, conor!
> [100/8192] greet me please using the `greet` function. my name is conor.
Hello, conor!
> [207/8192] great me please using the asynchronous `greet` function. my name is conor
Hello, conor!
> [317/8192] what functions can you do
Here are the functions I can perform:

1. **greet**: A function that generates a simple greeting for a given name.
2. **greet_coro**: This is like the greet function, but works asynchronously. 
```
