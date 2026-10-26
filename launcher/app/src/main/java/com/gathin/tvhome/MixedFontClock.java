package com.gathin.tvhome;

import android.content.Context;
import android.graphics.Typeface;
import android.os.Build;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.style.TypefaceSpan;
import android.widget.TextClock;

/**
 * A TextClock whose letters use a display font and whose digits keep the view's own typeface: a theme font such as
 * the trial Anurati has letters but no digits, so "24 OCTOBER" shows the 24 in the clock's font and OCTOBER in it.
 */
public class MixedFontClock extends TextClock {
    private Typeface letters;

    public MixedFontClock(Context context) {
        super(context);
    }

    void setLetterTypeface(Typeface face) {
        letters = face;
    }

    @Override
    public void setText(CharSequence text, BufferType type) {
        // TextView spans need API 28 for a Typeface; older sets keep the plain text.
        if (letters == null || text == null || Build.VERSION.SDK_INT < Build.VERSION_CODES.P) {
            super.setText(text, type);
            return;
        }
        SpannableString styled = new SpannableString(text);
        int start = -1;
        for (int i = 0; i <= text.length(); i++) {
            boolean letter = i < text.length() && Character.isLetter(text.charAt(i));
            if (letter && start < 0) start = i;
            if (!letter && start >= 0) {
                styled.setSpan(new TypefaceSpan(letters), start, i, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                start = -1;
            }
        }
        super.setText(styled, BufferType.SPANNABLE);
    }
}
