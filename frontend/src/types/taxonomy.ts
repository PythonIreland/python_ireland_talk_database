// frontend/src/types/taxonomy.ts
export interface Taxonomy {
  id: number;
  name: string;
  description: string;
  created_by: string;
  is_system: boolean;
  created_at: string;
  values: TaxonomyValue[];
}

export interface TaxonomyValue {
  id: number;
  taxonomy_id: number;
  value: string;
  description: string;
  color: string;
  is_active: boolean;
  created_at: string;
}

export interface TalkTags {
  talk_id: string;
  auto_tags: string[];
  manual_tags: Record<string, string[]>; // taxonomy_name -> tag_values[]
}

export interface CreateTaxonomyRequest {
  name: string;
  description?: string;
}

export interface UpdateTaxonomyRequest {
  name?: string;
  description?: string;
}

export interface CreateTaxonomyValueRequest {
  value: string;
  description?: string;
  color?: string;
}

export interface UpdateTaxonomyValueRequest {
  value?: string;
  description?: string;
  color?: string;
  is_active?: boolean;
}

export interface AddTagsRequest {
  taxonomy_value_ids: number[];
}

export interface ReplaceTalkTagsRequest {
  taxonomy_value_ids: number[];
}

export interface BulkTagOperation {
  action: "add" | "replace" | "remove";
  talk_id: string;
  taxonomy_value_ids: number[];
}

export interface TaxonomyAnalytics {
  taxonomy_id: number;
  taxonomy_name: string;
  total_values: number;
  total_usage: number;
  top_values: Array<{
    value_id: number;
    value: string;
    usage_count: number;
  }>;
}

export interface PopularTag {
  value_id: number;
  value: string;
  taxonomy_name: string;
  usage_count: number;
  color: string;
}

export interface AdvancedSearchParams {
  query?: string;
  taxonomy_filters?: Record<string, string[]>; // taxonomy_name -> values[]
  limit?: number;
  offset?: number;
}
