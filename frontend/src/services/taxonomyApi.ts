// frontend/src/services/taxonomyApi.ts
import { BACKEND_URL } from "../config";
import type {
  Taxonomy,
  TaxonomyValue,
  TalkTags,
  CreateTaxonomyRequest,
  UpdateTaxonomyRequest,
  CreateTaxonomyValueRequest,
  UpdateTaxonomyValueRequest,
  AddTagsRequest,
  ReplaceTalkTagsRequest,
  BulkTagOperation,
  TaxonomyAnalytics,
  PopularTag,
  AdvancedSearchParams,
} from "../types/taxonomy";
import type { ExplorerItem } from "../utils/api";

const API_BASE = `${BACKEND_URL}/api/v1/talks`;

/**
 * Taxonomy Management API
 */
export class TaxonomyAPI {
  // Taxonomy CRUD Operations
  static async getTaxonomies(): Promise<Taxonomy[]> {
    const response = await fetch(`${API_BASE}/taxonomies`);
    if (!response.ok) throw new Error("Failed to fetch taxonomies");
    return response.json();
  }

  static async createTaxonomy(data: CreateTaxonomyRequest): Promise<Taxonomy> {
    const response = await fetch(`${API_BASE}/taxonomies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error("Failed to create taxonomy");
    return response.json();
  }

  static async updateTaxonomy(
    id: number,
    data: UpdateTaxonomyRequest
  ): Promise<Taxonomy> {
    const response = await fetch(`${API_BASE}/taxonomies/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error("Failed to update taxonomy");
    return response.json();
  }

  static async deleteTaxonomy(id: number): Promise<void> {
    const response = await fetch(`${API_BASE}/taxonomies/${id}`, {
      method: "DELETE",
    });
    if (!response.ok) throw new Error("Failed to delete taxonomy");
  }

  // Taxonomy Value CRUD Operations
  static async createTaxonomyValue(
    taxonomyId: number,
    data: CreateTaxonomyValueRequest
  ): Promise<TaxonomyValue> {
    const response = await fetch(
      `${API_BASE}/taxonomies/${taxonomyId}/values`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }
    );
    if (!response.ok) throw new Error("Failed to create taxonomy value");
    return response.json();
  }

  static async updateTaxonomyValue(
    valueId: number,
    data: UpdateTaxonomyValueRequest
  ): Promise<TaxonomyValue> {
    const response = await fetch(`${API_BASE}/taxonomy-values/${valueId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error("Failed to update taxonomy value");
    return response.json();
  }

  static async deleteTaxonomyValue(valueId: number): Promise<void> {
    const response = await fetch(`${API_BASE}/taxonomy-values/${valueId}`, {
      method: "DELETE",
    });
    if (!response.ok) throw new Error("Failed to delete taxonomy value");
  }

  // Talk Tagging Operations
  static async getTalkTags(talkId: string): Promise<TalkTags> {
    const response = await fetch(`${API_BASE}/talks/${talkId}/tags`);
    if (!response.ok) throw new Error("Failed to fetch talk tags");
    return response.json();
  }

  static async addTagsToTalk(
    talkId: string,
    data: AddTagsRequest
  ): Promise<void> {
    const response = await fetch(`${API_BASE}/talks/${talkId}/tags/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error("Failed to add tags to talk");
  }

  static async replaceTalkTags(
    talkId: string,
    data: ReplaceTalkTagsRequest
  ): Promise<void> {
    const response = await fetch(`${API_BASE}/talks/${talkId}/tags`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error("Failed to replace talk tags");
  }

  static async removeTagFromTalk(
    talkId: string,
    valueId: number
  ): Promise<void> {
    const response = await fetch(
      `${API_BASE}/talks/${talkId}/tags/${valueId}`,
      {
        method: "DELETE",
      }
    );
    if (!response.ok) throw new Error("Failed to remove tag from talk");
  }

  // Bulk Operations
  static async bulkUpdateTalkTags(
    operations: BulkTagOperation[]
  ): Promise<void> {
    const response = await fetch(`${API_BASE}/talks/bulk-tag-operations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ operations }),
    });
    if (!response.ok) throw new Error("Failed to perform bulk tag operations");
  }

  // Analytics Operations
  static async getTaxonomyAnalytics(): Promise<TaxonomyAnalytics[]> {
    const response = await fetch(`${API_BASE}/analytics/taxonomy-usage`);
    if (!response.ok) throw new Error("Failed to fetch taxonomy analytics");
    return response.json();
  }

  static async getPopularTags(limit: number = 20): Promise<PopularTag[]> {
    const response = await fetch(
      `${API_BASE}/analytics/popular-tags?limit=${limit}`
    );
    if (!response.ok) throw new Error("Failed to fetch popular tags");
    return response.json();
  }

  static async getTaxonomyValueUsage(taxonomyId: number): Promise<
    Array<{
      value_id: number;
      value: string;
      usage_count: number;
    }>
  > {
    const response = await fetch(
      `${API_BASE}/analytics/taxonomies/${taxonomyId}/usage`
    );
    if (!response.ok) throw new Error("Failed to fetch taxonomy value usage");
    return response.json();
  }

  // Advanced Search
  static async advancedSearch(params: AdvancedSearchParams): Promise<{
    talks: ExplorerItem[];
    total: number;
  }> {
    const searchParams = new URLSearchParams();

    if (params.query) searchParams.append("query", params.query);
    if (params.limit) searchParams.append("limit", params.limit.toString());
    if (params.offset) searchParams.append("offset", params.offset.toString());

    // Add taxonomy filters
    if (params.taxonomy_filters) {
      for (const [taxonomyName, values] of Object.entries(
        params.taxonomy_filters
      )) {
        for (const value of values) {
          searchParams.append(`taxonomy_${taxonomyName}`, value);
        }
      }
    }

    const response = await fetch(`${API_BASE}/search/advanced?${searchParams}`);
    if (!response.ok) throw new Error("Failed to perform advanced search");
    return response.json();
  }

  // Initialize Default Taxonomies (for admin use)
  static async initializeDefaultTaxonomies(): Promise<void> {
    const response = await fetch(`${API_BASE}/taxonomies/initialize-defaults`, {
      method: "POST",
    });
    if (!response.ok)
      throw new Error("Failed to initialize default taxonomies");
  }
}
