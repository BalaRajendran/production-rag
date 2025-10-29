import { useState } from 'react';
import { Plus, Grid3x3, Info } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { QuickAccess } from './components/QuickAccess';
import { FileList } from './components/FileList';
import { LastModified } from './components/LastModified';
import { useDriveData } from './hooks/useDriveData';

function App() {
  const [activeTab, setActiveTab] = useState('my-drive');
  const { files, folders, loading } = useDriveData();

  const storageUsed = 60 * 1024 ** 3;
  const storageTotal = 115 * 1024 ** 3;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-lg font-medium text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        storageUsed={storageUsed}
        storageTotal={storageTotal}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header userName="James" />

        <main className="flex-1 overflow-y-auto">
          <div className="max-w-[1400px] mx-auto p-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-semibold text-gray-800">My Drive</h1>
                <button className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  <Plus className="w-5 h-5" />
                </button>
              </div>
              <div className="flex items-center gap-2">
                <button className="p-2 hover:bg-white rounded-lg transition-colors">
                  <Grid3x3 className="w-5 h-5 text-gray-600" />
                </button>
                <button className="p-2 hover:bg-white rounded-lg transition-colors">
                  <Info className="w-5 h-5 text-gray-600" />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-[1fr,280px] gap-6">
              <div>
                <QuickAccess folders={folders} />
                <FileList files={files} />
              </div>

              <div className="space-y-4">
                {files.length > 0 && (
                  <LastModified
                    fileName={files[0].name}
                    date={files[0].last_modified}
                  />
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
