When you need to handle response in an nonstandard way or add or change arguments 
before request, you can apply prepares and finalizers respectively.
                                                                     
## Preparers
Preparers are used for request preparation. That means add or change arguments 
before request. Preparers are usually used in [Routed Models](/learn/user_guide/oop_style.html#routed-models).
              
```python
@router.patch('/users/{id_}', skip_finalizer=True)
def update(
        self,
        name: str,
        job: str
) -> datetime.datetime:
    ...

@update.prepare
def _update_in(self, args: Args) -> Args:
    args.url = format_str(args.url, {'id_': self.id})
    return args
```
