// frontend/src/utils/api.ts
const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface ExplorerItem {
  id: string;
  title: string;
  description: string;
  date: string;
  platform: string; // 'pycon' | 'meetup' | 'youtube' | 'other'
  speakers?: string[];
  tags?: string[];
  auto_tags?: string[];
  manual_tags?: string[];
  source_url?: string;
  
  // Type-specific fields
  event_name?: string;     // PyConf
  room?: string;          // PyConf  
  venue_name?: string;    // Meetup
  city?: string;          // Meetup
  going_count?: number;   // Meetup
  group_name?: string;    // Meetup
}

export interface FetchExplorerItemsParams {
  from?: Date | null;
  to?: Date | null;
  search?: string;
  talk_types?: string[];
  tags?: string[];
  limit?: number;
  offset?: number;
}

export async function fetchExplorerItems(params: FetchExplorerItemsParams = {}): Promise<ExplorerItem[]> {
  const searchParams = new URLSearchParams();
  
  if (params.search) {
    searchParams.append('q', params.search);
  }
  
  if (params.talk_types) {
    params.talk_types.forEach(type => {
      searchParams.append('talk_types', type);
    });
  }
  
  if (params.tags) {
    params.tags.forEach(tag => {
      searchParams.append('tags', tag);
    });
  }
  
  if (params.limit) {
    searchParams.append('limit', params.limit.toString());
  }

  const url = `${API_BASE_URL}/talks/search?${searchParams.toString()}`;
  
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Transform backend data to frontend format
    return data.talks.map((talk: any) => ({
      id: talk.id,
      title: talk.title,
      description: talk.description,
      date: talk.event_date || talk.start_time || talk.created_at,
      platform: talk.talk_type,
      speakers: talk.speaker_names || [],
      tags: [...(talk.auto_tags || []), ...(talk.manual_tags || [])],
      auto_tags: talk.auto_tags || [],
      manual_tags: talk.manual_tags || [],
      source_url: talk.event_url || talk.source_url,
      
      // Type-specific fields
      event_name: talk.event_name,
      room: talk.room,
      venue_name: talk.venue_name,
      city: talk.city,
      going_count: talk.going_count,
      group_name: talk.group_name,
    }));
  } catch (error) {
    console.error('Error fetching explorer items:', error);
    return [];
  }
}

export async function fetchItemDetail(itemId: string): Promise<ExplorerItem | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/talks/search?q=id:${itemId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    if (data.talks.length === 0) {
      return null;
    }
    
    const talk = data.talks[0];
    return {
      id: talk.id,
      title: talk.title,
      description: talk.description,
      date: talk.event_date || talk.start_time || talk.created_at,
      platform: talk.talk_type,
      speakers: talk.speaker_names || [],
      tags: [...(talk.auto_tags || []), ...(talk.manual_tags || [])],
      auto_tags: talk.auto_tags || [],
      manual_tags: talk.manual_tags || [],
      source_url: talk.event_url || talk.source_url,
      
      event_name: talk.event_name,
      room: talk.room,
      venue_name: talk.venue_name,
      city: talk.city,
      going_count: talk.going_count,
      group_name: talk.group_name,
    };
  } catch (error) {
    console.error('Error fetching item detail:', error);
    return null;
  }
}

export async function fetchTags(): Promise<string[]> {
  // For now, return common tags - later we can add an endpoint to get all unique tags
  return [
    'AI/ML',
    'Web Development', 
    'Data Science',
    'Testing',
    'DevOps',
    'Python Core',
    'Django',
    'FastAPI',
    'Pandas',
    'NumPy',
    'Machine Learning',
    'Deep Learning',
    'API',
    'Database',
    'Async',
  ];
}

export async function updateItemTags(itemId: string, tags: string[]): Promise<void> {
  // TODO: Implement when we add tag update endpoint to backend
  console.log('Updating tags for item', itemId, 'with tags', tags);
  
  // For now, just log - we'll implement the backend endpoint later
  try {
    const response = await fetch(`${API_BASE_URL}/talks/${itemId}/tags`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ manual_tags: tags }),
    });
    
    if (!response.ok) {
      console.warn('Tag update endpoint not implemented yet');
    }
  } catch (error) {
    console.warn('Tag update not available yet:', error);
  }
}

export async function fetchTalkTypes(): Promise<string[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/talks/types`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.types;
  } catch (error) {
    console.error('Error fetching talk types:', error);
    return ['pycon', 'meetup'];
  }
}