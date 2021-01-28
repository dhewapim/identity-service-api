var api_product_scopes = String(context.getVariable('oauthv2accesstoken.OAuthV2.ClientCredentialsGenerateAccessToken.scope'));

var scopes_list = api_product_scopes.split(" ");
var regex = new RegExp("(urn:nhsd:apim:app:jwks:*)");
var filtered_application_restricted_scopes = scopes_list.filter(scope => {
    if (regex.test(scope)) {
        return scope;
    }
});
filtered_application_restricted_scopes = filtered_application_restricted_scopes.join(' ');
print(filtered_application_restricted_scopes);
context.setVariable('apigee.application_restricted_scopes', filtered_application_restricted_scopes);