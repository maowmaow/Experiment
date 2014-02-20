
var ultimatumApp = angular.module('ultimatumApp', ['ngCookies','ngResource']);

ultimatumApp.config(function($httpProvider) {
	$httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
});

ultimatumApp.run(function($http, $cookies) {
	$http.defaults.headers.post['X-CSRFToken'] = $cookies['csrftoken'];
	$http.defaults.headers.delete = { 'X-CSRFToken' : $cookies['csrftoken'] };
});

ultimatumApp.factory('roomSvc', ['$resource', function($resource) {
	return $resource('/ultimatum/api/:room_pk/:action');
}]);

ultimatumApp.factory('bidSvc', ['$resource', function($resource) {
	return $resource('/ultimatum/api/:room_pk/bid/:bid_pk');
}]);