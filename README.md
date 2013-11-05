Kivy / Google Maps integration
==============================

Example that shows how to integrate Google Maps within a Kivy application.
Currently works only on Android.

**Work in progress**

![ScreenShot](https://raw.github.com/tito/kivy-gmaps/master/screenshot.png)

Configuration
-------------

* Configure your `package.name` and `package.domain`. The sum of both should
  not be more than 20 characters, or Google Maps API will not work:

        package.name = kivygmaps
        package.domain = com.mr

* Follow the [Android Maps API v2 documentation](https://developers.google.com/maps/documentation/android/start#the_google_maps_api_key) to get your Android Maps API key
* Put your API Key into buildozer.spec in `[app:android.meta_data]` section as
  `com.google.android.maps.v2.API_KEY`:

        [app:android.meta_data]
        com.google.android.maps.v2.API_KEY = YOURAPIKEYHERE

Usage
-----

The `gmaps` module provide a `GMap` widget that you can directly use into your
application. Right now, you can add only one GMap per application, on an
transparent background. If you cover the background, the widget will not be
shown. Here is an hello world example:

```python
import gmaps
from kivy.app import App

class HelloGmaps(App):
    def build(self):
        self.map_widget = GMap()
        self.map_widget.bind(on_ready=self.create_some_markers)
        return self.map_widget

    def create_some_markers(self, map_widget):
        # get the google map interface
        sydney = map_widget.create_latlng(-33.867, 151.206)
        marker = map_widget.create_marker(
            title='Sydney',
            snippet='The most populous city in Autralia',
            position=sydney)
        map_widget.map.addMarker(marker)

if __name__ == '__main__':
    HelloGmaps().run()
```

### Threads

All the operation done on the map **must** be done within the internal thread
of the android widget. It means, you cannot interact directly from Kivy. You
can create object (LatLng, Marker..), but interact with the map must stay in
the map thread.

All the event fired by the `GMap` are happening in the map thread. For example,
if you bind to the `GMap.on_map_click`, your callback will be already in the
map thread. If you want to call a method within the map thread, you can use
`GMap.execute()` method. You cannot return values from it, and the call
will be asynchronous:

```python
map = GMap()
def my_func(...):
    pass
map.execute(my_func)
```

You can also decorate your function with `android.runnable.run_on_ui_thread`, or `GMap.run_on_ui_thread`:

```python
from android.runnable import run_on_ui_thread

@run_on_ui_thread
def set_position(self, lat, lng):
    pos = self.map_widget.create_latlng(lat, lng)
    self.map_widget.map.moveCamera(
        self.map_widget.camera_update_factory.newLatLngZoom(
        pos, 13))
```

When the Android Google Maps widget is created, it will fire an event name
`on_ready`. This is where you can create markers, change the camera, and so on.

### Events

Supported [Google Maps events](https://developers.google.com/maps/documentation/android/reference/com/google/android/gms/maps/GoogleMap) are:

* `on_camera_change(CameraPosition)` (not working yet)
* `on_info_window_click(Marker)`
* `on_map_click(LatLng)`
* `on_map_loaded()` (not working yet)
* `on_map_long_click(Marker)`
* `on_marker_click(Marker)`
* `on_marker_drag(Marker)`
* `on_marker_drag_end(Marker)`
* `on_marker_drag_start(Marker)`
* `on_my_location_button_click`

All the events are dispatched in the map thread, not the kivy main thread.

### Utils

The GMap have some methods to create java object easily, such as:

* `GMap.create_latlng(lat, lng)` - Create a [LatLng](https://developers.google.com/maps/documentation/android/reference/com/google/android/gms/maps/model/LatLng) object
* `GMap.create_marker(**options)` Create a [Marker](https://developers.google.com/maps/documentation/android/reference/com/google/android/gms/maps/model/Marker) object, with all the key=value in options

## Authors

- Mathieu Virbel, [Melting Rocks](http://meltingrocks.com/)
- Thomas Hansen, [Fresk](http://fresklabs.com)
