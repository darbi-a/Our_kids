importScripts('offline_pos/static/src/js/dexie.min.js');


const BLACKLIST_URLS = [
    '/hw_proxy',
    '/longpolling/poll',
    '/web/dataset/call_kw/pos.order/create_from_ui',
    '/web/dataset/call_kw/res.partner/create_from_ui',
    '/web/dataset/call_kw/pos.gift.coupon/search_coupon',
    '/web/dataset/call_kw/pos.gift.coupon/existing_coupon',
]

/**
 * Serializes a Request into a plain JS object.
 *
 * @param request
 * @returns Promise
 */
function serializeRequest(request) {
	  var serialized = {
		url: request.url,
		headers: serializeHeaders(request.headers),
		method: request.method,
		mode: request.mode,
		credentials: request.credentials,
		cache: request.cache,
		redirect: request.redirect,
		referrer: request.referrer
	  };

	  // Only if method is not `GET` or `HEAD` is the request allowed to have body.
	  if (request.method !== 'GET' && request.method !== 'HEAD') {
		return request.clone().text().then(function(body) {
		  serialized.body = body;
		  return Promise.resolve(serialized);
		});
	  }
	  return Promise.resolve(serialized);
}

/**
 * Serializes a Response into a plain JS object
 *
 * @param response
 * @returns Promise
 */
function serializeResponse(response) {
	  var serialized = {
		headers: serializeHeaders(response.headers),
		status: response.status,
		statusText: response.statusText,
		url: response.url
	  };

      return response.clone().json().then(function(body) {
          delete body.id
          var body = JSON.stringify(body)
          serialized.body = body;
          return Promise.resolve(serialized);
      });

}

/**
 * Serializes headers into a plain JS object
 *
 * @param headers
 * @returns object
 */
function serializeHeaders(headers) {
	var serialized = {};
	// `for(... of ...)` is ES6 notation but current browsers supporting SW, support this
	// notation as well and this is the only way of retrieving all the headers.
	for (var entry of headers.entries()) {
		serialized[entry[0]] = entry[1];
	}
	return serialized;
}

/**
 * Creates a Response from it's serialized version
 *
 * @param data
 * @returns Promise
 */
function deserializeResponse(data) {
    var init = { "status" : data.status , "statusText" : data.statusText , "url": data.url, "headers" : data.headers };
	return new Response(data.body, init);
}

/**
 * Saves the response for the given request eventually overriding the previous version
 *
 * @param data
 * @returns Promise
 */
function cachePut(request, response, store) {
	var key, data;

    serializeRequest(request.clone())
    .then(function(serializedRequest){
        body_json = JSON.parse(serializedRequest.body);
        delete body_json.id
        var key = JSON.stringify(body_json)
        return Promise.resolve(key);
    }).then(function(key){

        serializeResponse(response.clone())
        .then(function(serializedResponse) {
            data = serializedResponse;
            var entry = {
                key: key,
                response: data,
                timestamp: Date.now()
            };
            store
            .add(entry)
            .catch(function(error){
                store.update(entry.key, entry);
            });
        });

    })

}

function cachePutOrders(request, response, store) {
	var key, data;

    serializeRequest(request.clone())
    .then(function(serializedRequest){
        body_json = JSON.parse(serializedRequest.body);
        delete body_json.id
        delete body_json.params
        var key = JSON.stringify(body_json)
        return Promise.resolve(key);
    }).then(function(key){

        serializeResponse(response.clone())
        .then(function(serializedResponse) {
            data = serializedResponse;
            var entry = {
                key: key,
                response: data,
                timestamp: Date.now()
            };
            store
            .add(entry)
            .catch(function(error){
                store.update(entry.key, entry);
            });
        });

    })

}

/**
 * Returns the cached response for the given request or an empty 503-response  for a cache miss.
 *
 * @param request
 * @return Promise
 */
function cacheMatch(request,store,db) {
    return serializeRequest(request.clone())
    .then(function(serializedRequest){
        body_json = JSON.parse(serializedRequest.body);
        delete body_json.id
        var id = JSON.stringify(body_json)
        return Promise.resolve(id)
    })
	.then(function(id) {
        data = db.post_cache.where('key').equals(id).toArray();
		return  Promise.resolve(data);
	}).then(function(data){
		if (data  && data.length > 0) {
		    response = data[0].response;
		    return deserializeResponse(data[0].response);
		} else {
			return new Response('', {status: 503, statusText: 'Service Unavailable'});
		}
	});

}

function cacheMatchOrders(request,store,db) {
    return serializeRequest(request.clone())
    .then(function(serializedRequest){
        body_json = JSON.parse(serializedRequest.body);
        delete body_json.id
        delete body_json.params
        var id = JSON.stringify(body_json)
        return Promise.resolve(id)
    })
	.then(function(id) {
        data = db.post_cache.where('key').equals(id).toArray();
		return  Promise.resolve(data);
	}).then(function(data){
		if (data  && data.length > 0) {
		    response = data[0].response;
		    return deserializeResponse(data[0].response);
		} else {
			return new Response('', {status: 503, statusText: 'Service Unavailable'});
		}
	});

}

var CACHE_NAME = 'pos-v2';
var urlsToCache = [
  '/',

];

self.addEventListener('install', function(event) {
  // Perform install steps
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

var store_state = false;

self.addEventListener('fetch', function(event) {
//  console.log("'" + event.request.url + "',");
//  console.log(event.request.url + 'method: ' +event.request.method);
    if(event.request.referrer.indexOf('/pos/web') != -1 || event.request.referrer.indexOf('/static') != -1 || event.request.referrer.indexOf('/web/content') != -1){
         store_state = true;
    }
    else{
        store_state = false;
        console.log(event.request.referrer);
        console.log(event.request.url);
    }

  console.log(store_state);
  console.log(event.request);
  if(event.request.method === "GET" &&  event.request.url.indexOf('/web/binary/company_logo') == -1 )
  {
      event.respondWith(
        caches.match(event.request)
          .then(function(response) {
            // Cache hit - return response
            if (response) {
              return response;
            }

            // IMPORTANT: Clone the request. A request is a stream and
            // can only be consumed once. Since we are consuming this
            // once by cache and once by the browser for fetch, we need
            // to clone the response.
            var fetchRequest = event.request.clone();

            return fetch(fetchRequest).then(
              function(response) {
                // Check if we received a valid response
                if(!response || response.status !== 200 || response.type !== 'basic') {
                  return response;
                }

                // IMPORTANT: Clone the response. A response is a stream
                // and because we want the browser to consume the response
                // as well as the cache consuming the response, we need
                // to clone it so we have two streams.
                var responseToCache = response.clone();

                caches.open(CACHE_NAME)
                  .then(function(cache) {
                    if(store_state){
                        cache.put(event.request, responseToCache);
                    }
                  });
                return response;
              }
            );
          })
        );
   }
   else if(event.request.method === "POST" && event.request.url.indexOf('/web/dataset/call_kw/pos.order/search_read') == -1){

		// Init the cache. We use Dexie here to simplify the code. You can use any other
		// way to access IndexedDB of course.
		var db = new Dexie("post_cache");
		db.version(1).stores({
			post_cache: 'key,response,timestamp'
		})

		event.respondWith(
			// First try to fetch the request from the server
			fetch(event.request.clone())
			.then(function(response) {
                for(var url of BLACKLIST_URLS) {
                    if (event.request.url.indexOf(url) != -1) {
                        console.log("Blacklisted URL: " + event.request.url);
                        console.log(response.clone());
                        return response;
                    }
                }
				// If it works, put the response into IndexedDB
				if(store_state){
                    cachePut(event.request.clone(), response.clone(), db.post_cache);
                    }
				return response;
			})
			.catch(function() {
				// If it does not work, return the cached response. If the cache does not
				// contain a response for our request, it will give us a 503-response
				return cacheMatch(event.request.clone(), db.post_cache,db);

			})
		);
   }
   else if(event.request.method === "POST" && event.request.url.indexOf('/web/dataset/call_kw/pos.order/search_read') != -1){

		// Init the cache. We use Dexie here to simplify the code. You can use any other
		// way to access IndexedDB of course.
		var db = new Dexie("post_cache");
		db.version(1).stores({
			post_cache: 'key,response,timestamp'
		})

		event.respondWith(
			// First try to fetch the request from the server
			fetch(event.request.clone())
			.then(function(response) {
                if(store_state){
                    cachePutOrders(event.request.clone(), response.clone(), db.post_cache);
                }
				return response;
			})
			.catch(function() {
				// If it does not work, return the cached response. If the cache does not
				// contain a response for our request, it will give us a 503-response
				return cacheMatchOrders(event.request.clone(), db.post_cache,db);

			})
		);
   }
   else if(event.request.method === "GET" &&  event.request.url.indexOf('/web/binary/company_logo' )){
        var fetchRequest = event.request.clone();
		event.respondWith(
			fetch("/get/company_logo")
			.then(
              function(response) {

                var responseToCache = response.clone();

                caches.open(CACHE_NAME)
                  .then(function(cache) {
                    if(store_state){
                        cache.put("/get/company_logo", responseToCache);
                        }
                  });
                return response;
            })
            .catch(function() {
               caches.match("/get/company_logo")
              .then(function(response) {
                // Cache hit - return response
                if (response) {
                  return response;
                }

            })

        })
        )
    }

});

