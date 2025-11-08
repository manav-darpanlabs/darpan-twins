# Quick Start Guide - Updated Streamlit App

## What Changed?

Your Streamlit app now has 5 major improvements:

1. **Fixed UI Overlaps** - Clean results display, no more text overlapping
2. **Reset Button** - "Run Another Experiment" button to easily restart
3. **Detailed Stats** - Twin counts, percentages, and decision criteria breakdown
4. **Formatted Factors** - 2-3 word factors instead of long sentences
5. **Better City Selector** - 8 Indian cities by default with auto-weather fetch
6. **Image Previews** - See uploaded images and parsed data before running

---

## How to Run

### Start the App

```bash
cd /Users/aniketniranjanmishra/Desktop/Darpan\ Labs/mvp_manav/p1
source .venv/bin/activate
streamlit run app_streamlit.py
```

The app will open at: **http://localhost:8501**

---

## New User Flow

### Step 1: City & Upload

**City Selection** (Improved!)
- Choose from dropdown: Mumbai, Delhi, Bangalore, Chennai, etc.
- Weather fetches automatically - no button needed!
- See weather card with icons immediately
- Or use "search custom city" for other locations

**Upload Cards** (New Preview!)
- Upload Card A and Card B images
- See image preview immediately
- Click "Start experiment" to parse
- View parsed data in expandable sections before running

### Step 2: Running

- Progress bar shows LLM processing
- Same as before - automated

### Step 3: Results (Completely Redesigned!)

**Summary Section**
- "Experiment Summary: 10 digital twins simulated"

**Aggregate Results** (Fixed Overlaps!)
- Card A: 8 twins (80.0%) ████████░░
- Card B: 2 twins (20.0%) ██░░░░░░░░
- Tie: 0 twins (0.0%) ░░░░░░░░░░

**Top Factors** (New Formatting!)
- Side-by-side columns for A and B
- Formatted as 2-3 words: "Higher Rating", "Lower Price", etc.
- Shows count and percentage: "6 twins (75%)"

**Decision Criteria Breakdown** (New!)
- Price: A=5, B=3, Tie=2
- Delivery: A=7, B=2, Tie=1
- Fit: A=6, B=3, Tie=1
- Trust: A=8, B=1, Tie=1

**Reset Button** (New!)
- Click "🔄 Run Another Experiment" to start over
- Preserves XP, clears all experiment data
- Returns to Step 1

**Detailed Data**
- Expandable table with per-twin breakdown
- Same as before

---

## Testing

### Run Unit Tests

```bash
.venv/bin/python test_app_changes.py
```

Expected output:
```
Testing format_factor()...
  ✓ 8 passed, 0 failed

Testing aggregate_results()...
  ✓ All checks passed

Testing DEFAULT_CITIES...
  ✓ All checks passed

============================================================
✓ All tests passed!
============================================================
```

---

## Key Files Modified

- **app_streamlit.py** - Main application (~320 lines changed)
- **test_app_changes.py** - New test suite (201 lines)
- **CHANGES_SUMMARY.md** - Detailed changelog
- **QUICK_START.md** - This file

---

## Troubleshooting

### Issue: "No module named 'streamlit'"
**Solution**: Activate virtual environment first
```bash
source .venv/bin/activate
```

### Issue: Weather not fetching
**Solution**: Check internet connection and .env file has API keys

### Issue: Images not uploading
**Solution**: Ensure file is PNG/JPG/JPEG and <200MB

### Issue: Results look wrong
**Solution**:
1. Check dual_results in session state
2. Run test_app_changes.py to verify functions work
3. Clear browser cache and refresh

---

## What's Next?

Optional future enhancements (not implemented yet):

1. **Export Results** - Download CSV/JSON of experiment data
2. **Experiment History** - Compare multiple experiments
3. **Charts** - Visual breakdown of checks (pie/bar charts)
4. **Mobile Optimization** - Better responsive design
5. **Error Handling** - User-friendly error messages

---

## Questions?

- Check [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) for detailed technical info
- Review code comments in `app_streamlit.py`
- Run tests: `test_app_changes.py`

**Status**: ✅ Production Ready - All tests passing
