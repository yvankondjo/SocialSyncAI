import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// Types
export type Channel = {
  id: string;
  name: string;
  network: 'linkedin' | 'instagram' | 'x' | 'facebook' | 'tiktok';
  avatarUrl: string;
};

export type Asset = {
  id: string;
  name: string;
  kind: 'image' | 'video';
  url: string;
  thumb: string;
  size: number;
  dimensions: { w: number; h: number };
  createdAt: Date;
  tags: string[];
  network?: string;
};

export type Post = {
  id: string;
  title?: string;
  content: string;
  channels: Channel[];
  assets: Asset[];
  scheduledAt?: Date;
  status: 'draft' | 'scheduled' | 'queued' | 'sent' | 'failed';
  createdAt: Date;
  updatedAt: Date;
};

export type Draft = {
  id: string;
  content: string;
  channels: Channel[];
  assets: Asset[];
  scheduledAt?: Date;
  createdAt: Date;
  updatedAt: Date;
};

// Store interfaces
interface PostsStore {
  posts: Post[];
  addPost: (post: Omit<Post, 'id' | 'createdAt' | 'updatedAt'>) => void;
  updatePost: (id: string, updates: Partial<Post>) => void;
  deletePost: (id: string) => void;
  getPost: (id: string) => Post | undefined;
}

interface AssetsStore {
  assets: Asset[];
  addAsset: (asset: Omit<Asset, 'id' | 'createdAt'>) => void;
  updateAsset: (id: string, updates: Partial<Asset>) => void;
  deleteAsset: (id: string) => void;
  getAsset: (id: string) => Asset | undefined;
}

interface ChannelsStore {
  channels: Channel[];
  addChannel: (channel: Channel) => void;
  updateChannel: (id: string, updates: Partial<Channel>) => void;
  deleteChannel: (id: string) => void;
  getChannel: (id: string) => Channel | undefined;
}

interface DraftsStore {
  drafts: Draft[];
  currentDraft: Draft | null;
  saveDraft: (draft: Omit<Draft, 'id' | 'createdAt' | 'updatedAt'>) => void;
  updateDraft: (id: string, updates: Partial<Draft>) => void;
  deleteDraft: (id: string) => void;
  setCurrentDraft: (draft: Draft | null) => void;
  clearCurrentDraft: () => void;
}

// Default data
const defaultChannels: Channel[] = [
  {
    id: '1',
    name: 'SocialSync LinkedIn',
    network: 'linkedin',
    avatarUrl: '/diverse-woman-portrait.png',
  },
  {
    id: '2',
    name: 'SocialSync Instagram',
    network: 'instagram',
    avatarUrl: '/thoughtful-man.png',
  },
  {
    id: '3',
    name: 'SocialSync X',
    network: 'x',
    avatarUrl: '/woman-blonde.png',
  },
  {
    id: '4',
    name: 'SocialSync Facebook',
    network: 'facebook',
    avatarUrl: '/man-beard.png',
  },
];

const defaultAssets: Asset[] = [
  {
    id: '1',
    name: 'Product Launch Hero',
    kind: 'image',
    url: '/placeholder.svg?height=400&width=600',
    thumb: '/placeholder.svg?height=200&width=300',
    size: 245760,
    dimensions: { w: 1200, h: 800 },
    createdAt: new Date(2024, 11, 10),
    tags: ['product', 'hero', 'launch'],
    network: 'linkedin',
  },
  {
    id: '2',
    name: 'Team Meeting Video',
    kind: 'video',
    url: '/placeholder.svg?height=400&width=600',
    thumb: '/placeholder.svg?height=200&width=300',
    size: 15728640,
    dimensions: { w: 1920, h: 1080 },
    createdAt: new Date(2024, 11, 9),
    tags: ['team', 'meeting', 'corporate'],
    network: 'instagram',
  },
];

const defaultPosts: Post[] = [
  {
    id: '1',
    title: 'Product Launch Announcement',
    content: 'Excited to announce our new AI-powered social media tool!',
    channels: [defaultChannels[0], defaultChannels[1]],
    assets: [defaultAssets[0]],
    scheduledAt: new Date(2024, 11, 15, 10, 0),
    status: 'scheduled',
    createdAt: new Date(2024, 11, 10),
    updatedAt: new Date(2024, 11, 10),
  },
  {
    id: '2',
    content: 'Weekly tips for better social media engagement',
    channels: [defaultChannels[2]],
    assets: [],
    scheduledAt: new Date(2024, 11, 16, 14, 30),
    status: 'draft',
    createdAt: new Date(2024, 11, 9),
    updatedAt: new Date(2024, 11, 9),
  },
];

// Posts Store
export const usePostsStore = create<PostsStore>()(
  persist(
    (set, get) => ({
      posts: defaultPosts,
      addPost: postData => {
        const newPost: Post = {
          ...postData,
          id: Date.now().toString(),
          createdAt: new Date(),
          updatedAt: new Date(),
        };
        set(state => ({ posts: [...state.posts, newPost] }));
      },
      updatePost: (id, updates) => {
        set(state => ({
          posts: state.posts.map(post =>
            post.id === id
              ? { ...post, ...updates, updatedAt: new Date() }
              : post
          ),
        }));
      },
      deletePost: id => {
        set(state => ({ posts: state.posts.filter(post => post.id !== id) }));
      },
      getPost: id => {
        return get().posts.find(post => post.id === id);
      },
    }),
    {
      name: 'socialsync-posts',
      storage: createJSONStorage(() => localStorage),
      partialize: state => ({ posts: state.posts }),
    }
  )
);

// Assets Store
export const useAssetsStore = create<AssetsStore>()(
  persist(
    (set, get) => ({
      assets: defaultAssets,
      addAsset: assetData => {
        const newAsset: Asset = {
          ...assetData,
          id: Date.now().toString(),
          createdAt: new Date(),
        };
        set(state => ({ assets: [...state.assets, newAsset] }));
      },
      updateAsset: (id, updates) => {
        set(state => ({
          assets: state.assets.map(asset =>
            asset.id === id ? { ...asset, ...updates } : asset
          ),
        }));
      },
      deleteAsset: id => {
        set(state => ({
          assets: state.assets.filter(asset => asset.id !== id),
        }));
      },
      getAsset: id => {
        return get().assets.find(asset => asset.id === id);
      },
    }),
    {
      name: 'socialsync-assets',
      storage: createJSONStorage(() => localStorage),
      partialize: state => ({ assets: state.assets }),
    }
  )
);

// Channels Store
export const useChannelsStore = create<ChannelsStore>()(
  persist(
    (set, get) => ({
      channels: defaultChannels,
      addChannel: channel => {
        set(state => ({ channels: [...state.channels, channel] }));
      },
      updateChannel: (id, updates) => {
        set(state => ({
          channels: state.channels.map(channel =>
            channel.id === id ? { ...channel, ...updates } : channel
          ),
        }));
      },
      deleteChannel: id => {
        set(state => ({
          channels: state.channels.filter(channel => channel.id !== id),
        }));
      },
      getChannel: id => {
        return get().channels.find(channel => channel.id === id);
      },
    }),
    {
      name: 'socialsync-channels',
      storage: createJSONStorage(() => localStorage),
      partialize: state => ({ channels: state.channels }),
    }
  )
);

// Drafts Store
export const useDraftsStore = create<DraftsStore>()(
  persist(
    (set, get) => ({
      drafts: [],
      currentDraft: null,
      saveDraft: draftData => {
        const newDraft: Draft = {
          ...draftData,
          id: Date.now().toString(),
          createdAt: new Date(),
          updatedAt: new Date(),
        };
        set(state => ({ drafts: [...state.drafts, newDraft] }));
      },
      updateDraft: (id, updates) => {
        set(state => ({
          drafts: state.drafts.map(draft =>
            draft.id === id
              ? { ...draft, ...updates, updatedAt: new Date() }
              : draft
          ),
        }));
      },
      deleteDraft: id => {
        set(state => ({
          drafts: state.drafts.filter(draft => draft.id !== id),
          currentDraft:
            state.currentDraft?.id === id ? null : state.currentDraft,
        }));
      },
      setCurrentDraft: draft => {
        set({ currentDraft: draft });
      },
      clearCurrentDraft: () => {
        set({ currentDraft: null });
      },
    }),
    {
      name: 'socialsync-drafts',
      storage: createJSONStorage(() => localStorage),
      partialize: state => ({
        drafts: state.drafts,
        currentDraft: state.currentDraft,
      }),
    }
  )
);
