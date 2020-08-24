## About
The `powersimdata.data_access` package contains implementations of storage to
be used by the simulation framework generally. By providing a consistent api
for any given set of data, we can decouple the storage medium from application
logic.

Currently, there are csv and sql implementations for the scenario list and
execute list.

## Usage
To try this out, use the `stack.yml` provided in the tests directory to run a
local instance of postgres, plus an admin ui. The integration tests for the db layer are run against this instance, and you can also connect to it with `psql`, the standard cli tool for interacting with postgres.

Start the container using the following command, taken from the postgres
[docs](https://github.com/docker-library/docs/blob/master/postgres/README.md).
```
docker-compose -f stack.yml up
```

Note - the schema are not automatically created (or part of source control) at this point, so to run the tests you'll need to do this manually. Improvements on this are forthcoming. 
