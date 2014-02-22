
var stockApp = angular.module('stockApp', ['ngCookies','ngResource']);

stockApp.config(function($httpProvider) {
	$httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
});

stockApp.run(function($http, $cookies) {
	$http.defaults.headers.post['X-CSRFToken'] = $cookies['csrftoken'];
	$http.defaults.headers.delete = { 'X-CSRFToken' : $cookies['csrftoken'] };
});

stockApp.factory('stockSvc', ['$resource', function($resource) {
	return $resource('/stock/api/admin/stock/:stock_pk');
}]);

stockApp.factory('bidSvc', ['$resource', function($resource) {
	return $resource('/ultimatum/api/:room_pk/bid/:bid_pk');
}]);
