## About
The `powersimdata.data_access` package contains implementations of storage to
be used by the simulation framework generally. By providing a consistent api
for any given set of data, we can decouple the storage medium from application
logic.

Currently, there are csv and sql implementations for the scenario list and
execute list.

## Usage
To try this out, use the `stack.yml` to run a local instance of postgres, plus an admin ui. 
The integration tests for the db layer are run against this instance, and you can also connect to it with `psql`, 
the standard cli tool for interacting with postgres.

Start the container using the following command, taken from the postgres
[docs](https://github.com/docker-library/docs/blob/master/postgres/README.md).
```
docker-compose -f stack.yml up
```


## Schema creation
When the container starts, it will run the `.sql` files in the mounted volume
to initialize the database.

To do this manually, run the container then do the following:

```
# connect to container, use password from stack.yml
 psql -U postgres -h localhost
```

In the psql shell, run `\i sql/schema.sql` (make sure to `cd` to this directory first)
to create the necessary objects. After this, you should be connected to the `psd` database, 
and running `\dt` should confirm the tables have been created.


## Database management
At the moment this is kind of a placeholder section. But for anyone interested,
the stack.yml setup includes a container running an admin ui which can be used to explore the
containerized db. You can view this at http://localhost:8080 and login using the credentials
from the file.
