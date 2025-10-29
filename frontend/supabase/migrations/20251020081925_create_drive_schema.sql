/*
  # Google Drive Dashboard Schema

  1. New Tables
    - `files`
      - `id` (uuid, primary key)
      - `name` (text, file name)
      - `type` (text, file type/extension)
      - `size` (bigint, file size in bytes)
      - `owner_id` (uuid, references auth.users)
      - `folder_id` (uuid, optional parent folder reference)
      - `file_url` (text, storage URL)
      - `last_modified` (timestamptz)
      - `created_at` (timestamptz)
    
    - `shared_files`
      - `id` (uuid, primary key)
      - `file_id` (uuid, references files)
      - `shared_with_user_id` (uuid, references auth.users)
      - `permission` (text, 'view' or 'edit')
      - `created_at` (timestamptz)
    
    - `quick_access_folders`
      - `id` (uuid, primary key)
      - `name` (text, folder name)
      - `description` (text, folder description)
      - `owner_id` (uuid, references auth.users)
      - `created_at` (timestamptz)
    
    - `folder_members`
      - `id` (uuid, primary key)
      - `folder_id` (uuid, references quick_access_folders)
      - `user_id` (uuid, references auth.users)
      - `avatar_url` (text, user avatar)
      - `created_at` (timestamptz)

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users to manage their own files
    - Add policies for shared file access
*/

-- Files table
CREATE TABLE IF NOT EXISTS files (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  type text NOT NULL DEFAULT '',
  size bigint DEFAULT 0,
  owner_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  folder_id uuid,
  file_url text DEFAULT '',
  last_modified timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);

ALTER TABLE files ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own files"
  ON files FOR SELECT
  TO authenticated
  USING (auth.uid() = owner_id);

CREATE POLICY "Users can insert own files"
  ON files FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update own files"
  ON files FOR UPDATE
  TO authenticated
  USING (auth.uid() = owner_id)
  WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can delete own files"
  ON files FOR DELETE
  TO authenticated
  USING (auth.uid() = owner_id);

-- Shared files table
CREATE TABLE IF NOT EXISTS shared_files (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  file_id uuid REFERENCES files(id) ON DELETE CASCADE,
  shared_with_user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  permission text DEFAULT 'view',
  created_at timestamptz DEFAULT now()
);

ALTER TABLE shared_files ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view files shared with them"
  ON shared_files FOR SELECT
  TO authenticated
  USING (auth.uid() = shared_with_user_id);

CREATE POLICY "File owners can share their files"
  ON shared_files FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM files
      WHERE files.id = file_id
      AND files.owner_id = auth.uid()
    )
  );

CREATE POLICY "File owners can update sharing"
  ON shared_files FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM files
      WHERE files.id = file_id
      AND files.owner_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM files
      WHERE files.id = file_id
      AND files.owner_id = auth.uid()
    )
  );

CREATE POLICY "File owners can delete sharing"
  ON shared_files FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM files
      WHERE files.id = file_id
      AND files.owner_id = auth.uid()
    )
  );

-- Quick access folders table
CREATE TABLE IF NOT EXISTS quick_access_folders (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text DEFAULT '',
  owner_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE quick_access_folders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own folders"
  ON quick_access_folders FOR SELECT
  TO authenticated
  USING (auth.uid() = owner_id);

CREATE POLICY "Users can insert own folders"
  ON quick_access_folders FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update own folders"
  ON quick_access_folders FOR UPDATE
  TO authenticated
  USING (auth.uid() = owner_id)
  WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can delete own folders"
  ON quick_access_folders FOR DELETE
  TO authenticated
  USING (auth.uid() = owner_id);

-- Folder members table
CREATE TABLE IF NOT EXISTS folder_members (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  folder_id uuid REFERENCES quick_access_folders(id) ON DELETE CASCADE,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  avatar_url text DEFAULT '',
  created_at timestamptz DEFAULT now()
);

ALTER TABLE folder_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Folder owners can view members"
  ON folder_members FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM quick_access_folders
      WHERE quick_access_folders.id = folder_id
      AND quick_access_folders.owner_id = auth.uid()
    )
  );

CREATE POLICY "Folder owners can add members"
  ON folder_members FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM quick_access_folders
      WHERE quick_access_folders.id = folder_id
      AND quick_access_folders.owner_id = auth.uid()
    )
  );

CREATE POLICY "Folder owners can remove members"
  ON folder_members FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM quick_access_folders
      WHERE quick_access_folders.id = folder_id
      AND quick_access_folders.owner_id = auth.uid()
    )
  );