var id_token_acr = context.getVariable('jwt.DecodeJWT.FromExternalIdToken.decoded.claim.acr');
var api_product_scopes = String(context.getVariable('original_scope'));
id_token_acr = ':' + id_token_acr.slice(0, 4).toLowerCase() + ':';

if (api_product_scopes == 'null') {
    api_product_scopes = String(context.getVariable('oauthv2accesstoken.OAuthV2.TokenExchangeGenerateAccessToken.scope'));
}

var scopes_list = api_product_scopes.split(" ");
var filtered_user_restricted_scopes = scopes_list.filter(scope => {
    if (api_product_scopes.includes(id_token_acr)) {
        return scope;
    }
});
filtered_user_restricted_scopes = filtered_user_restricted_scopes.join(' ');
context.setVariable('apigee.user_restricted_scopes', filtered_user_restricted_scopes);