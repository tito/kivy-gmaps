'''
Google Maps integration
=======================

The goal of this widget is to integrate and interact with the Google Map API v2.
The android component will be placed at the right pos/size of the Kivy widget,
as an Underlay (behind the Kivy surface, not above/overlay). The widget must
stay in the right orientation / axis-aligned, or the placement of the android
widget will not work.

Here is the settings to add in buildozer::

    [app:android.meta_data]
    com.google.android.maps.v2.API_KEY = YOURAPIKEYHERE
    surface.transluent = 1
    surface.depth = 16

.. warning::

    The Kivy's Window.clearcolor will be automatically set to transparent, or
    the Google Maps widget will not be displayed at all.
    
'''

__all__ = ('GMap', 'GMapException')

from kivy.uix.widget import Widget
from kivy.clock import Clock
from android.runnable import run_on_ui_thread
from jnius import autoclass, cast, PythonJavaClass, java_method
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.logger import Logger

PythonActivity = autoclass('org.renpy.android.PythonActivity')
Surface = autoclass('android.view.Surface')
Button = autoclass('android.widget.Button')
LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
LinearLayout = autoclass('android.widget.LinearLayout')
GooglePlayServicesUtil = autoclass('com.google.android.gms.common.GooglePlayServicesUtil')
InterceptLinearLayout = autoclass('com.meltingrocks.InterceptLinearLayout')
MapsInitializer = autoclass('com.google.android.gms.maps.MapsInitializer')
MapView = autoclass('com.google.android.gms.maps.MapView')
LatLng = autoclass('com.google.android.gms.maps.model.LatLng')
MarkerOptions = autoclass('com/google.android.gms.maps.model.MarkerOptions')
CameraUpdateFactory = autoclass('com/google.android.gms.maps.CameraUpdateFactory')


class GMapException(Exception):
    pass


class TouchListener(PythonJavaClass):
    __javacontext__ = 'app'
    __javainterfaces__ = [
        'com/meltingrocks/InterceptLinearLayout$OnInterceptTouchListener']

    def __init__(self, listener):
        super(TouchListener, self).__init__()
        self.listener = listener

    @java_method('(Landroid/view/MotionEvent;)Z')
    def onTouch(self, event):
        x = event.getX(0)
        y = event.getY(0)
        return self.listener(x, y)


class GoogleMapEventListener(PythonJavaClass):
    __javacontext__ = 'app'
    __javainterfaces__ = [
        # part of the latest SDK (31 october 2013), not yet downloaded.
        #'com/google/android/gms/maps/GoogleMap$OnCameraChangeListener',
        #'com/google/android/gms/maps/GoogleMap$OnMapLoadedCallback',
        'com/google/android/gms/maps/GoogleMap$OnInfoWindowClickListener',
        'com/google/android/gms/maps/GoogleMap$OnMapClickListener',
        'com/google/android/gms/maps/GoogleMap$OnMapLongClickListener',
        'com/google/android/gms/maps/GoogleMap$OnMarkerClickListener',
        'com/google/android/gms/maps/GoogleMap$OnMyLocationButtonClickListener']

    def __init__(self, listener):
        super(GoogleMapEventListener, self).__init__()
        self.listener = listener

    @java_method('(Lcom/google/android/gms/maps/model/CameraPosition;)V')
    def onCameraChange(self, position):
        self.listener.dispatch('on_camera_change', position)

    @java_method('(Lcom/google/android/gms/maps/model/Marker;)V')
    def onInfoWindowClick(self, marker):
        self.listener.dispatch('on_info_window_click', marker)

    @java_method('(Lcom/google/android/gms/maps/model/LatLng;)V')
    def onMapClick(self, point):
        self.listener.dispatch('on_map_click', point)

    @java_method('()V')
    def onMapLoaded(self):
        self.listener.dispatch('on_map_loaded')

    @java_method('(Lcom/google/android/gms/maps/model/LatLng;)V')
    def onMapLongClick(self, point):
        self.listener.dispatch('on_map_long_click', point)

    @java_method('(Lcom/google/android/gms/maps/model/Marker;)Z')
    def onMarkerClick(self, marker):
        return self.listener.dispatch('on_marker_click', marker)

    @java_method('(Lcom/google/android/gms/maps/model/Marker;)V')
    def onMarkerDrag(self, marker):
        self.listener.dispatch('on_marker_drag', marker)

    @java_method('(Lcom/google/android/gms/maps/model/Marker;)V')
    def onMarkerDragEnd(self, marker):
        self.listener.dispatch('on_marker_drag_end', marker)

    @java_method('(Lcom/google/android/gms/maps/model/Marker;)V')
    def onMarkerDragStart(self, marker):
        self.listener.dispatch('on_marker_drag_start', marker)

    @java_method('()Z')
    def onMyLocationButtonClick(self):
        return self.listener.dispatch('on_my_location_button_click')


class AndroidWidgetHolder(Widget):
    '''Act as a placeholder for an Android widget.
    It will automatically add / remove the android view depending if the widget
    view is set or not. The android view will act as an overlay, so any graphics
    instruction in this area will be covered by the overlay.
    '''

    view = ObjectProperty(allownone=True)
    '''Must be an Android View
    '''

    def __init__(self, **kwargs):
        self._old_view = None
        from kivy.core.window import Window
        self._wh = Window.height
        self._listener = TouchListener(self._on_touch_listener)

        #from kivy.app import App
        #App.get_running_app().bind(on_resume=self._reorder)
        super(AndroidWidgetHolder, self).__init__(**kwargs)

    '''
    @run_on_ui_thread
    def _reorder(self, *args):
        print 'reorder neened?', args
        view = PythonActivity.mView
        parent = cast(LinearLayout, view.getParent())
        parent.bringChildToFront(view)
        parent.requestLayout()
        parent.invalidate()
    '''

    def _get_view_bbox(self):
        x, y = self.to_window(*self.pos)
        w, h = self.size
        #return (0, 0, int(w), int(h))
        return [int(z) for z in [x, self._wh - y - self.height, self.width, self.height]]

    def reposition_view(self):
        x, y, w, h = self._get_view_bbox()
        params = self.view.getLayoutParams()
        if not self.view or not params:
            return
        params.width = w
        params.height = h
        self.view.setLayoutParams(params)
        self.view.setX(x)
        self.view.setY(y)

    def on_view(self, instance, view):
        print 'on_view', instance, view
        if self._old_view is not None:
            print 'removing the oldest'
            layout = cast(LinearLayout, self._old_view.getParent())
            layout.removeView(self._old_view)
            self._old_view = None

        if view is None:
            return

        activity = PythonActivity.mActivity
        x, y, w, h = self._get_view_bbox()
        print 'add the view to our content view', (w, h, x, y)

        print '--> create interceptlinearlayout'
        layout = InterceptLinearLayout(activity)
        print '--> set interceptlinearlayout'
        layout.setInterceptTouchListener(self._listener)
        print '--> link'
        layout.addView(view, LayoutParams(-1, -1))
        #layout.addView(PythonActivity.mView, LayoutParams(-1, -1))

        view = layout
        #parent = cast(LinearLayout, PythonActivity.mView.getParent())
        #parent.addView(view, 0, LayoutParams(w, h))
        activity.addContentView(view, LayoutParams(w, h))
        print '--> done'

        view.setX(x)
        view.setY(y)
        self._old_view = view
        self.canvas.ask_update()

        #Clock.schedule_once(self._set, 0)

    def _set(self, *args):
        self.view.setOnTouchListener(self._on_touch_listener)
        self.view.setOnGenericMotionListener(self._on_touch_listener)

    def on_size(self, instance, size):
        if self.view:
            self.reposition_view()

    def on_x(self, instance, x):
        if self.view:
            self.reposition_view()

    def on_y(self, instance, y):
        if self.view:
            self.reposition_view()

    #
    # Determine if the touch is going to be for us, or for the android widget.
    # If we find any Kivy widget behind the touch (except us), then avoid the
    # dispatching to the map. The touch will be received by the widget later.
    #

    def _on_touch_listener(self, x, y):
        # invert Y !
        from kivy.core.window import Window
        y = Window.height - y
        # x, y are in Window coordinate. Try to select the widget under the
        # touch.
        widget = None
        for child in reversed(Window.children):
            widget = self._pick(child, x, y)
            if not widget:
                continue
        if self is not widget:
            return True

    def _pick(self, widget, x, y):
        ret = None
        if widget.collide_point(x, y):
            ret = widget
            x2, y2 = widget.to_local(x, y)
            for child in reversed(widget.children):
                ret = self._pick(child, x2, y2) or ret
        return ret


class GMap(Widget):

    __events__ = (
        'on_camera_change',
        'on_info_window_click',
        'on_map_click',
        'on_map_loaded',
        'on_map_long_click',
        'on_marker_click',
        'on_marker_drag',
        'on_marker_drag_end',
        'on_marker_drag_start',
        'on_my_location_button_click',
        
        # kivy/map_widget event, to know when it's ready.
        'on_ready'
        )

    def __init__(self, **kwargs):
        # force Window clearcolor to be transparent.
        from kivy.core.window import Window
        Window.clearcolor = (0, 0, 0, 0)

        super(GMap, self).__init__(**kwargs)
        self._holder = AndroidWidgetHolder()
        self._context = PythonActivity.mActivity

        ret = GooglePlayServicesUtil.isGooglePlayServicesAvailable(self._context)
        if ret != 0:
            raise GMapException('Google Play Service are not available '
                    '(code: 0x{:x})'.format(ret))

        self.add_widget(self._holder)
        self.bind(
            size=self._holder.setter('size'),
            pos=self._holder.setter('pos'))

        self._event_listener = GoogleMapEventListener(self)

        Clock.schedule_once(self.create_view, 0)

    @run_on_ui_thread
    def create_view(self, *args):
        MapsInitializer.initialize(self._context)

        self._view = view = MapView(self._context)

        # faster sizing
        view.onCreate(None)
        view.onResume()
        w, h = map(int, self.size)
        view.measure(w, h)
        view.layout(0, 0, w, h)

        # bind our map and holder view
        self._gmap = gmap = view.getMap()
        self._holder.view = view

        # register the events

        listener = self._event_listener
        # part of the lastest SDK, not yet downloaded (31 october 2013)
        #gmap.setOnCameraChangeListener(listener)
        #gmap.setOnMapLoadedCallback(listener)
        gmap.setOnInfoWindowClickListener(listener)
        gmap.setOnMapClickListener(listener)
        gmap.setOnMapLongClickListener(listener)
        gmap.setOnMarkerClickListener(listener)
        gmap.setOnMarkerDragListener(listener)
        gmap.setOnMyLocationButtonClickListener(listener)

        # dispatch an event to inform that the gmap is available to use
        self.dispatch('on_ready')

    @property
    def map(self):
        '''Return a `GoogleMap` object.

        https://developers.google.com/maps/documentation/android/reference/com/google/android/gms/maps/GoogleMap
        '''
        return self._gmap

    @property
    def camera_update_factory(self):
        '''Return the `CameraUpdateFactory`
        '''
        return CameraUpdateFactory

    #
    # utilities
    #

    def create_latlng(self, lat, lng):
        return LatLng(lat, lng)

    def create_marker(self, **options):
        '''Available options:

        - position: LatLng
        - rotation: float
        - snippet: str
        - title: str
        - visible: bool
        - icon: BitmapDescriptor
        - flat: bool
        - draggable: bool
        - anchor: float, float
        - alpha: float

        Returns a correct MarkerOptions object
        '''
        marker = MarkerOptions()
        for key, value in options.iteritems():
            marker = getattr(marker, key)(value)
        return marker


    #
    # default events
    #

    def on_camera_change(self, position):
        Logger.info('Gmap: on_camera_change()')
        pass

    def on_info_window_click(self, marker):
        Logger.info('Gmap: on_info_window_click()')
        pass

    def on_map_click(self, point):
        Logger.info('Gmap: on_map_click()')
        pass

    def on_map_loaded(self):
        Logger.info('Gmap: on_map_loaded)')
        pass

    def on_map_long_click(self, point):
        Logger.info('Gmap: on_map_long_click)')
        pass

    def on_marker_click(self, marker):
        Logger.info('Gmap: on_marker_click)')
        pass

    def on_marker_drag(self, marker):
        Logger.info('Gmap: on_marker_drag)')
        pass

    def on_marker_drag_end(self, marker):
        Logger.info('Gmap: on_marker_drag_end)')
        pass

    def on_marker_drag_start(self, marker):
        Logger.info('Gmap: on_marker_drag_start)')
        pass

    def on_my_location_button_click(self):
        Logger.info('Gmap: on_my_location_button_click)')
        pass

    def on_ready(self):
        Logger.info('Gmap: on_ready()')
