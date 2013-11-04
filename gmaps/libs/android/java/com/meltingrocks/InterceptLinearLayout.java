package com.meltingrocks;

import android.widget.LinearLayout;
import android.content.Context;
import android.view.MotionEvent;

public class InterceptLinearLayout extends LinearLayout {

	private OnInterceptTouchListener listener;

	public interface OnInterceptTouchListener {
		boolean onTouch(MotionEvent ev);
	}

	public InterceptLinearLayout(Context context) {
		super(context);
	}

	public void setInterceptTouchListener(OnInterceptTouchListener listener) {
		this.listener = listener;
	}

	@Override
	public boolean onInterceptTouchEvent(MotionEvent event) {
		if ( this.listener != null )
			return this.listener.onTouch(event);
		return false;
	}
}
