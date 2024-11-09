# Parameters

Request parameters are functions returning an object used to provide the parameter metadata before request, such as
param type, validation, alias, etc.

These functions include:

- Query
- Body
- Path
- Form
- File
- Header
- Cookie

You can import them directly from `sensei`

```python
from sensei import Query, Body, Path, Form, File, Header, Cookie
```

There are two ways how to use them:

=== "Annotated"
    ```python
    @router.get('/users/{id_}')
    def get_user(id_: Annotated[int, Path()]) -> User:
        pass
    ```

=== "Direct"
    ```python
    @router.get('/users/{id_}')
    def get_user(id_: int = Path()) -> User:
        pass
    ```
            
    

:::sensei.Query
:::sensei.Body
:::sensei.Path
:::sensei.Form
:::sensei.File
:::sensei.Header
:::sensei.Cookie