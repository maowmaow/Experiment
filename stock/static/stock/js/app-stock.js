
var stockApp = angular.module('stockApp', ['ngCookies','ngResource']);

stockApp.config(function($httpProvider) {
	$httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
});

stockApp.run(function($http, $cookies) {
	$http.defaults.headers.post['X-CSRFToken'] = $cookies['csrftoken'];
	$http.defaults.headers.delete = { 'X-CSRFToken' : $cookies['csrftoken'] };
});

stockApp.factory('gameSvc', ['$resource', function($resource) {
	return $resource('/designforinstinctsgames/stock/api/admin/game/:game_pk/:action');
}]);

stockApp.factory('marketSvc', ['$resource', function($resource) {
	return $resource('/designforinstinctsgames/stock/api/market/:game_pk');
}]);

stockApp.factory('clientSvc', ['$resource', function($resource) {
	return $resource('/designforinstinctsgames/stock/api/client/portfolio/:order_pk');
}]);
