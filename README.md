# phonikud-tts-study

## Setup Supabase

1. Create a new Supabase project at https://supabase.com
2. Go to SQL Editor and run this query to create the table:

```sql
CREATE TABLE "phonikud-user-study" (
  id BIGSERIAL PRIMARY KEY,
  data JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);
```

3. Get your project URL and anon key from Settings > API
4. Update `web/config.json` with your real Supabase credentials
5. Deploy your app and collect responses!

## Generate Reports

1. Install Python dependencies:
```bash
cd report
pip install -r requirements.txt
```

2. Set environment variables and run:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-service-role-key"
export SUPABASE_TABLE="phonikud-user-study"
python main.py
```

This will create a timestamped JSON report with:
- **Summary**: Total submissions, model rankings, user language distribution
- **Individual data**: All raw submissions for detailed analysis