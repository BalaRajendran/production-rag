import { HardDrive, Monitor, Users, Clock, Trash2, Star, RotateCcw } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  storageUsed: number;
  storageTotal: number;
}

export function Sidebar({ activeTab, onTabChange, storageUsed, storageTotal }: SidebarProps) {
  const menuItems = [
    { id: 'my-drive', icon: HardDrive, label: 'My Drive' },
    { id: 'computers', icon: Monitor, label: 'Computers' },
    { id: 'shared', icon: Users, label: 'Shared with Me' },
    { id: 'recent', icon: Clock, label: 'Recents' },
    { id: 'trash', icon: Trash2, label: 'Trash' },
    { id: 'starred', icon: Star, label: 'Starred' },
    { id: 'backups', icon: RotateCcw, label: 'Backups' },
  ];

  const usedGB = (storageUsed / (1024 ** 3)).toFixed(2);
  const totalGB = (storageTotal / (1024 ** 3)).toFixed(0);
  const percentUsed = (storageUsed / storageTotal * 100).toFixed(1);

  return (
    <div className="w-64 bg-blue-700 text-white h-screen flex flex-col">
      <div className="p-6">
        <div className="flex items-center gap-2 mb-8">
          <HardDrive className="w-6 h-6" />
          <h1 className="text-xl font-semibold">Goodle Drive</h1>
        </div>

        <button className="w-full bg-white text-blue-700 rounded-full py-3 px-6 font-medium hover:bg-blue-50 transition-colors">
          Upload New Files
        </button>
      </div>

      <nav className="flex-1 px-4">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                activeTab === item.id
                  ? 'bg-blue-600 text-white'
                  : 'text-blue-100 hover:bg-blue-600/50'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-sm font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-6 border-t border-blue-600">
        <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
          <HardDrive className="w-4 h-4" />
          STORAGE DETAILS
        </h3>
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 bg-blue-400 rounded-full"></div>
            <span>Storage</span>
          </div>
          <div className="text-xs text-blue-200">
            {usedGB} GB of {totalGB} used
          </div>
          <div className="w-full bg-blue-600 rounded-full h-2 overflow-hidden">
            <div
              className="bg-blue-300 h-full rounded-full"
              style={{ width: `${percentUsed}%` }}
            ></div>
          </div>
          <div className="text-xs text-blue-200">
            {(storageTotal - storageUsed) / (1024 ** 3) >= 0
              ? `${((storageTotal - storageUsed) / (1024 ** 3)).toFixed(2)} GB of ${totalGB} GB`
              : '0 GB'}
          </div>
          <button className="text-xs text-blue-200 hover:text-white flex items-center gap-1">
            Upgrade Storage
            <span className="text-lg leading-none">→</span>
          </button>
        </div>
      </div>
    </div>
  );
}
