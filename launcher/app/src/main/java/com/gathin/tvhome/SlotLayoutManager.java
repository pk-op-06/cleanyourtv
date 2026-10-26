package com.gathin.tvhome;

import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

/**
 * A layout's dock (config-<name>.json logo_slots): each app's tile centred on a fixed point of a 1920x1080 screen,
 * scaled to the real one, and the App library button centred on more_slot. No scrolling: every item is laid out.
 * Items past the slots (and the button with no more_slot) are left out.
 */
final class SlotLayoutManager extends RecyclerView.LayoutManager {
    private final float[][] slots;
    private final float[] moreSlot;
    private RecyclerView rv;

    SlotLayoutManager(float[][] slots, float[] moreSlot) {
        this.slots = slots;
        this.moreSlot = moreSlot;
    }

    @Override
    public RecyclerView.LayoutParams generateDefaultLayoutParams() {
        return new RecyclerView.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    @Override
    public void onAttachedToWindow(RecyclerView view) {
        super.onAttachedToWindow(view);
        rv = view;
    }

    @Override
    public void onLayoutChildren(RecyclerView.Recycler recycler, RecyclerView.State state) {
        detachAndScrapAttachedViews(recycler);
        if (rv == null || getWidth() == 0) return;
        // Slots are screen points; this view starts below the header, so shift them into its coordinates.
        int[] at = new int[2];
        rv.getLocationInWindow(at);
        float scale = rv.getRootView().getWidth() / 1920f;
        int count = state.getItemCount();
        for (int i = 0; i < count; i++) {
            boolean more = i == count - 1 && i >= slots.length && moreSlot != null;
            if (i >= slots.length && !more) break;
            float[] p = more ? moreSlot : slots[i];
            View child = recycler.getViewForPosition(i);
            addView(child);
            View card = child.findViewById(R.id.card);
            int w;
            int cardTop;
            int cardH;
            if (card != null) {
                // An app tile: the card is centred on the point; its name may reach to the right of it.
                View name = child.findViewById(R.id.name);
                ViewGroup.MarginLayoutParams nameLp = (ViewGroup.MarginLayoutParams) name.getLayoutParams();
                int cardW = card.getLayoutParams().width;
                cardH = card.getLayoutParams().height;
                w = Math.max(cardW, nameLp.leftMargin + nameLp.width);
                child.measure(View.MeasureSpec.makeMeasureSpec(w, View.MeasureSpec.EXACTLY),
                        View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
                cardTop = child.getPaddingTop();
                int left = Math.round(p[0] * scale - at[0] - cardW / 2f);
                int top = Math.round(p[1] * scale - at[1] - cardTop - cardH / 2f);
                layoutDecorated(child, left, top, left + w, top + child.getMeasuredHeight());
            } else {
                // The App library row: its button is centred in the row, so a row twice the point's x centres it there.
                w = Math.round(2 * p[0] * scale - at[0] * 2);
                child.measure(View.MeasureSpec.makeMeasureSpec(Math.max(1, w), View.MeasureSpec.EXACTLY),
                        View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
                int top = Math.round(p[1] * scale - at[1] - child.getMeasuredHeight() / 2f);
                layoutDecorated(child, 0, top, w, top + child.getMeasuredHeight());
            }
        }
    }

    @Override
    public boolean canScrollVertically() {
        return false;
    }

    @Override
    public void smoothScrollToPosition(@NonNull RecyclerView recyclerView, RecyclerView.State state, int position) {
        // Every item is on screen already.
    }
}
