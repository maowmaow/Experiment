
var ultimatumApp = angular.module('ultimatumApp', ['ngCookies','ngResource']);

ultimatumApp.config(function($httpProvider) {
	$httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
});

ultimatumApp.run(function($http, $cookies) {
	$http.defaults.headers.post['X-CSRFToken'] = $cookies['csrftoken'];
	$http.defaults.headers.delete = { 'X-CSRFToken' : $cookies['csrftoken'] };
});

ultimatumApp.factory('gameSvc', ['$resource', function($resource) {
	return $resource('/designforinstinctsgames/ultimatum/api/admin/game/:game_pk/:action');
}]);

ultimatumApp.factory('clientSvc', ['$resource', function($resource) {
	return $resource('/designforinstinctsgames/ultimatum/api/client/:bid_pk');
}]);

ultimatumApp.factory('summarySvc', ['$resource', function($resource) {
	return $resource('/designforinstinctsgames/ultimatum/api/summary/:game_pk');
}]);

ultimatumApp.factory('scoreSvc', ['$resource', function($resource) {
	return $resource('/designforinstinctsgames/ultimatum/api/score/:game_pk');
}]);

