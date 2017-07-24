<dl>
	<dt><H2>List install</H2></dt>
</dl>
```sudo pip3 install virtualenv```

```virtualenv venv```

```source venv/bin/activate or  deactivate```

```pip install -r  requirements.txt```

<dl>
	<dt><H2>Create db</H2></dt>
</dl>

```python manage.py db init```

```python manage.py db migrate -m "initial migration"```

```python manage.py db upgrade```

<dl>
	<dt><H2>Run flask </H2></dt>
</dl>

```python3 manage.py runserver```
