var id_token_acr = context.getVariable('jwt.DecodeJWT.FromSubjectTokenFormParam.decoded.claim.acr');
var api_product_scopes = String(context.getVariable('original_scope'));
if (idTokenIssuer == "nhsCis2") {
    id_token_acr = ':' + id_token_acr.slice(0, 4).toLowerCase() + ':';   
}
else {
    id_token_acr = ':' + id_token_acr.slice(0, 2).toLowerCase() + ':'; 
}


if (api_product_scopes == 'null') {
    api_product_scopes = String(context.getVariable('oauthv2accesstoken.OAuthV2.TokenExchangeGenerateAccessToken.scope'));
}

var scopes_list = api_product_scopes.split(" ");
var regex = new RegExp(id_token_acr);
var filtered_user_restricted_scopes = scopes_list.filter(scope => {
    if (regex.test(scope)) {
        return scope;
    }
});
filtered_user_restricted_scopes = filtered_user_restricted_scopes.join(' ');
context.setVariable('apigee.user_restricted_scopes', filtered_user_restricted_scopes);