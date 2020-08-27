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

## Schema creation
To get a working local database, run the container then do the following:

```
# connect to container, use password from stack.yml
 psql -U postgres -h localhost
```

Once in the `psql` shell, you can create the database using `CREATE DATABASE
psd;` then connect to it with `\c psd`. Make sure there is a file called
`schema.sql` in your current directory then run `\i schema.sql`. Now if you run
`\dt` you should see the tables have been created, and should be able to run
the integration tests. 
