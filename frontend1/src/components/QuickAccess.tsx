import { QuickAccessFolder } from '../lib/supabase';

interface QuickAccessProps {
  folders: QuickAccessFolder[];
}

export function QuickAccess({ folders }: QuickAccessProps) {
  const colors = ['bg-blue-600', 'bg-white border border-gray-200', 'bg-white border border-gray-200'];

  return (
    <div className="mb-8">
      <h2 className="text-sm font-semibold text-gray-700 mb-4">QUICK ACCESS</h2>
      <div className="grid grid-cols-3 gap-4">
        {folders.map((folder, index) => (
          <div
            key={folder.id}
            className={`${colors[index] || 'bg-white border border-gray-200'} ${
              index === 0 ? 'text-white' : 'text-gray-700'
            } rounded-2xl p-6 hover:shadow-lg transition-shadow cursor-pointer`}
          >
            <div className="mb-4">
              <div className="text-xs font-semibold mb-2 opacity-75">SHARED WITH</div>
              <div className="flex -space-x-2">
                {folder.members?.slice(0, 4).map((member, idx) => (
                  <div
                    key={member.id}
                    className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 border-2 border-white flex items-center justify-center text-xs font-bold"
                  >
                    {String.fromCharCode(65 + idx)}
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div className="text-xs font-semibold mb-1 opacity-75">FOLDER</div>
              <div className="text-sm font-semibold">{folder.name}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
