/*
  # Setup demo data

  1. Changes
    - Remove foreign key constraints for demo
    - Update RLS policies for public access
    - Insert sample data with valid UUIDs
  
  2. Security
    - Public read access for demo purposes
    - Write operations still restricted
*/

-- Drop foreign key constraints
DO $$ 
BEGIN
  ALTER TABLE files DROP CONSTRAINT IF EXISTS files_owner_id_fkey;
  ALTER TABLE quick_access_folders DROP CONSTRAINT IF EXISTS quick_access_folders_owner_id_fkey;
  ALTER TABLE shared_files DROP CONSTRAINT IF EXISTS shared_files_shared_with_user_id_fkey;
  ALTER TABLE folder_members DROP CONSTRAINT IF EXISTS folder_members_user_id_fkey;
EXCEPTION
  WHEN undefined_object THEN NULL;
END $$;

-- Update RLS policies
DROP POLICY IF EXISTS "Users can view own files" ON files;
DROP POLICY IF EXISTS "Users can view own folders" ON quick_access_folders;
DROP POLICY IF EXISTS "Folder owners can view members" ON folder_members;
DROP POLICY IF EXISTS "Users can view files shared with them" ON shared_files;

CREATE POLICY "Public read files" ON files FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Public read folders" ON quick_access_folders FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Public read members" ON folder_members FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Public read shared" ON shared_files FOR SELECT TO anon, authenticated USING (true);

-- Insert sample folders
INSERT INTO quick_access_folders (id, name, description)
VALUES 
  ('11111111-1111-1111-1111-111111111111', 'Design Files', 'Design project assets'),
  ('22222222-2222-2222-2222-222222222222', 'Google Photos', 'Photo collection'),
  ('33333333-3333-3333-3333-333333333333', 'Training Materials', 'Educational resources')
ON CONFLICT (id) DO NOTHING;

-- Insert sample folder members
INSERT INTO folder_members (folder_id, user_id, avatar_url)
VALUES 
  ('11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'avatar1.jpg'),
  ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', 'avatar2.jpg'),
  ('11111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333', 'avatar3.jpg'),
  ('22222222-2222-2222-2222-222222222222', '44444444-4444-4444-4444-444444444444', 'avatar4.jpg'),
  ('22222222-2222-2222-2222-222222222222', '55555555-5555-5555-5555-555555555555', 'avatar5.jpg'),
  ('22222222-2222-2222-2222-222222222222', '66666666-6666-6666-6666-666666666666', 'avatar6.jpg'),
  ('33333333-3333-3333-3333-333333333333', '77777777-7777-7777-7777-777777777777', 'avatar7.jpg'),
  ('33333333-3333-3333-3333-333333333333', '88888888-8888-8888-8888-888888888888', 'avatar8.jpg'),
  ('33333333-3333-3333-3333-333333333333', '99999999-9999-9999-9999-999999999999', 'avatar9.jpg')
ON CONFLICT DO NOTHING;

-- Insert sample files
INSERT INTO files (name, type, size, last_modified)
VALUES 
  ('Weekly Report Docs', 'docx', 20971520, '2019-09-09 04:30:00'),
  ('Design Checklist.xlsx', 'xlsx', 20971520, '2019-09-09 04:30:00'),
  ('Weekly-reports.pdf', 'pdf', 20971520, '2019-09-09 04:30:00'),
  ('Wedding Planner List.doc', 'doc', 20971520, '2019-09-09 04:30:00'),
  ('Team 3B Picture.jpg', 'jpg', 20971520, '2019-09-09 04:30:00'),
  ('Team Rent Picture.jpg', 'jpg', 20971520, '2019-09-09 04:30:00')
ON CONFLICT DO NOTHING;