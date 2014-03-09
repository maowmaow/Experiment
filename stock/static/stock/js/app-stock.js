
var stockApp = angular.module('stockApp', ['ngCookies','ngResource']);

stockApp.config(function($httpProvider) {
	$httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
});

stockApp.run(function($http, $cookies) {
	$http.defaults.headers.post['X-CSRFToken'] = $cookies['csrftoken'];
	$http.defaults.headers.delete = { 'X-CSRFToken' : $cookies['csrftoken'] };
});

stockApp.factory('gameSvc', ['$resource', function($resource) {
	return $resource('/stock/api/admin/game/:action');
}]);

stockApp.factory('marketSvc', ['$resource', function($resource) {
	return $resource('/stock/api/market');
}]);

stockApp.factory('clientSvc', ['$resource', function($resource) {
	return $resource('/stock/api/client/portfolio/:order_pk');
}]);
