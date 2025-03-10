# Deploying a new API

An API in PostgREST needs a few things to happen.

1. A JWT secret needs to be loaded into the PostgREST environment.
2. We need to tear down what was
3. We need to stand it back up again

# Creating a JWT secret

The command

```
fac create_api_jwt <role> <passphrase>
```

creates a JWT secret. The passphrase must be [at least 32 characters long](https://postgrest.org/en/v10.2/tutorials/tut1.html#:~:text=32%20characters%20long.-,Note,-Unix%20tools%20can).

For example:

```
fac create_api_jwt api_fac_gov mooE1Olp7u3xwgeDihtrjX14vbX9fH27
```

This will create the JWT

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYXBpX2ZhY19nb3ZfYW5vbiIsImNyZWF0ZWQiOiIyMDIzLTA3LTE0VDIxOjA0OjA2LjEyMDU0OCIsImV4cGlyZXMiOiIyMDI0LTAxLTE0VDIxOjA0OjA2LjEyMDUyMCIsImV4cCI6MTcwNTI2NjI0Nn0.cu2EVrP5X5u6uxVffeHLDNI24pfYyyICKD3wm1UtWts
```

This has three pieces:

```
header.payload.signature
```

**The data can be decoded without the passphrase.** So, a JWT token is not a way of *encrypting* data. Do not put any privileged information in a JWT.

However, without the passphrase, the signature cannot be verified. PostgREST will not accept a JWT as valid that does not have a good signature. Therefore, it should be the case that only JWTs we create, with this tool, signed with a passphrase we know, can be accepted by our stack as valid.

We pass `role` and `exp`, which are fields that PostgREST expect. We add two human-readable fields, `created` and `expires`. All tokens generated with this tool expire after 6 months, and must be refreshed at api.data.gov. If we don't refresh the token, api.data.gov (meaning api.fac.gov) will stop working.

## Using the JWT token

For symmetric use, that passphrase must be loaded into a GH Secret, and that secret deployed to our environments via Terraform. In this way, our PostgREST container knows how to verify the integrity of JWTs that are sent to us.

Our JWT only lives at api.data.gov. We will put it in the `Authorization: Bearer <jwt>` header. In this way, only API requests that come through api.data.gov (meaning requests that go to api.fac.gov) will be executed by PostgREST. All other queries, from all other sources, will be rejected.

It is important that the role you choose matches the role we expect for public queries. Our schemas are attached to the role `api_fac_gov`.

For example:

```
curl -X GET -H "Authorization: Bearer ${JWT}" "${API_FAC_URL}/general?limit=1"
```

should return one item from the general view. API_FAC_URL might be `http://localhost:3000` in testing locally, or `https://api.fac.gov` when working live.

### Limiting access

We use the `X-Api-Roles` header from api.data.gov to determine some levels of access.

https://api-umbrella.readthedocs.io/en/latest/admin/api-backends/http-headers.html

the stored procedure

```
has_tribal_data_access()
```

checks this header, and if the correct role is present (`fac_gov_tribal_data_access`), we will accept the query as being privileged. The role has to be attached to the key by an administrator.

## Standing up / tearing down

With each deployment of the stack, we should tear down and stand up the entire API.

1. `fac drop_deprecated_schema_and_views` will tear down any deprecated APIs. Always run it.
1. `fac drop_api_schema` will tear down the active schema and everything associated with it.
2. `fac create_api_schema` will create roles and the schema.
3. `fac create_api_views` will create the views on the data.

With this sequence, we completely tear down old *and* current APIs, as well as associated roles. Then, we stand them up again, including all roles. This guarantees that every deploy is a complete, fresh instantiation of the API, and any changes that may have been made to views, functions, or privileges are caught.

In other words: the API should always be stood up from a "blank slate" in the name of stateless deploys.

# API versions

When adding a new API version:

1. Create a copy of an existing API directory within `FAC/backend/dissemination/api` and name it with your version bump of choice.
   - For all files within this directory, replace all instances of the old API version with your new version.
2. Update `terraform/shared/modules/env/postgrest.tf` to use the new API version.
3. Update `live` and `deprecated` in `FAC/backend/dissemination/api_versions.py`.
4. Update `docker-compose.yml` and `docker-compose-web.yml`:
   - Change the values of `PGRST_DB_SCHEMAS` to your new API version. If previous versions of the API are needed, make the value a comma separated list and append your version to it. The first entry is the default, so only add to the front of the list if we are certain the schema should become the new default. See details on this [here](https://postgrest.org/en/stable/references/api/schemas.html#multiple-schemas)
      - This is likely true of TESTED patch version bumps (v1_0_0 to v1_0_1), and *maybe* minor version bumps (v1_0_0 to v1_1_0). MAJOR bumps require change management messaging.
5. If previous versions of the API are needed, `APIViewTests` will need to be updated. At the time of writing this, it only tests the default API.

# Using VS Code REST Client Plugin to Test API

## Installation:
1. In your Visual Studio Code, go to the Extensions Marketplace and search for **REST Client**.
4. Click **Install** and follow the steps to install one of the "REST Client".

## How to Use:
Once the REST Client extension is installed, you can create a `.http` or `.rest` file in your project and write your API queries directly within that file.

## Sample API Request:

Here’s an example of how to query your API using the REST Client:

```http
GET {{scheme}}://{{api_url}}/function_name_or_view_name_plus_params_if_any
authorization: Bearer {{YOUR_JWT_TOKEN}}     
x-api-user-id: {{your_api_user_id}}
accept-profile: target_api_profile
x-api-key: {{YOUR_API_GOV_KEY}}
```

## Key Details:
- **`authorization`**: The `Bearer {{YOUR_JWT_TOKEN}}` token is mandatory. Use the same JWT token used in Cypress tests from the code base. Without this token, the request will be flagged as anonymous and require extra steps to create an anonymous role in the local environment.
  
- **`x-api-user-id`**: Mandatory in some cases, depending on the API function. Search for the function in the code base to find where to get the correct value for `x-api-user-id`. Check keys like `support_administrative_key_uuids` and `dissemination_tribalapiaccesskeyids` for reference.

- **`accept-profile`**: Specifies the API version/profile. The current default is `api_v1_0_3`. You can check available profiles and deprecated versions in `backend/dissemination/api_versions.py`.

- **`x-api-key`**: An API key can be requested by following the steps described [here](https://www.fac.gov/api/).

## Example:

```http
GET http://localhost:3000/general?limit=1&is_public=eq.false
authorization: Bearer {{CYPRESS_API_GOV_JWT}}
x-api-user-id: 00112233-4455-6677-8899-aabbccddeeff
accept-profile: admin_api_v1_1_0
x-api-key: abcdefghijklmnop
```

This will send a request to `http://localhost:3000/general` with the provided headers and params.
Check `backend/support/api/admin_api_v1_1_0/` for more examples.


# End-to-end workbook testing

### How to run the workbook generator:
```
docker compose run web python manage.py generate_workbook_files
  --year 22 \
  --output <your_output_directory> \
  --dbkey 100010
```
- `year` is optional and defaults to `22`.
- The `output` directory will be created if it doesn't already exist.
