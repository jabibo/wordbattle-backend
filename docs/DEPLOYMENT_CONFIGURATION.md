# WordBattle Backend Deployment Configuration

## Database Configuration

### Database Password
- **Secret Name**: `prod-db-password`
- **Location**: Google Cloud Secret Manager
- **Usage**: Store the correct database password securely
- **Important**: Always use the password from Secret Manager, not hardcoded values

### Database Settings
- **Database Name**: `wordbattle_prod` (not `wordbattle_db`)
- **Database User**: `wordbattle`
- **Connection**: The wordbattle database user password must match the secret value

## Cloud Run Service Configuration

The service must have these environment variables and secrets configured:

### Environment Variables
```bash
DB_HOST=<cloud-sql-instance-connection-name>
DB_PORT=5432
DB_NAME=wordbattle_prod
DB_USER=wordbattle
```

### Secret References
```bash
DB_PASSWORD=projects/<project-id>/secrets/prod-db-password/versions/latest
```

## Key Points to Remember

1. **Always use the password from Secret Manager**, not hardcoded values
2. **Database name must be `wordbattle_prod`** for production
3. **The wordbattle database user password must match the secret value**
4. **Cloud Run service needs both environment variables and secret references**

## Deployment Commands

When deploying, ensure:
- Secret Manager contains the correct `prod-db-password`
- Cloud Run service references the secret properly
- Database connection uses `wordbattle_prod` as the database name
- User `wordbattle` has the correct password from the secret

This configuration ensures the backend can properly connect to the database and function correctly.

## Verification

To verify the configuration:
1. Check that the secret exists in Secret Manager
2. Verify Cloud Run service has the correct environment variables
3. Test database connectivity from the deployed service
4. Confirm the service can read from the `wordbattle_prod` database
