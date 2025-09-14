// frontend/src/contexts/TaxonomyContext.tsx
import React, { createContext, useContext, useState, useEffect } from "react";
import type { ReactNode } from "react";
import { TaxonomyAPI } from "../services/taxonomyApi";
import type { Taxonomy, TaxonomyValue, PopularTag } from "../types/taxonomy";

interface TaxonomyContextType {
  // State
  taxonomies: Taxonomy[];
  popularTags: PopularTag[];
  loading: boolean;
  error: string | null;

  // Actions
  refreshTaxonomies: () => Promise<void>;
  refreshPopularTags: () => Promise<void>;
  createTaxonomy: (name: string, description?: string) => Promise<Taxonomy>;
  updateTaxonomy: (
    id: number,
    name?: string,
    description?: string
  ) => Promise<Taxonomy>;
  deleteTaxonomy: (id: number) => Promise<void>;
  createTaxonomyValue: (
    taxonomyId: number,
    value: string,
    description?: string,
    color?: string
  ) => Promise<TaxonomyValue>;
  updateTaxonomyValue: (
    valueId: number,
    updates: Partial<TaxonomyValue>
  ) => Promise<TaxonomyValue>;
  deleteTaxonomyValue: (valueId: number) => Promise<void>;

  // Utility functions
  getTaxonomyById: (id: number) => Taxonomy | undefined;
  getTaxonomyByName: (name: string) => Taxonomy | undefined;
  getValueById: (id: number) => TaxonomyValue | undefined;
  getSystemTaxonomies: () => Taxonomy[];
  getUserTaxonomies: () => Taxonomy[];
}

const TaxonomyContext = createContext<TaxonomyContextType | undefined>(
  undefined
);

interface TaxonomyProviderProps {
  children: ReactNode;
}

export const TaxonomyProvider: React.FC<TaxonomyProviderProps> = ({
  children,
}) => {
  const [taxonomies, setTaxonomies] = useState<Taxonomy[]>([]);
  const [popularTags, setPopularTags] = useState<PopularTag[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshTaxonomies = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await TaxonomyAPI.getTaxonomies();
      setTaxonomies(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load taxonomies"
      );
    } finally {
      setLoading(false);
    }
  };

  const refreshPopularTags = async () => {
    try {
      const data = await TaxonomyAPI.getPopularTags(20);
      setPopularTags(data);
    } catch (err) {
      console.error("Failed to load popular tags:", err);
    }
  };

  const createTaxonomy = async (
    name: string,
    description?: string
  ): Promise<Taxonomy> => {
    try {
      setError(null);
      const newTaxonomy = await TaxonomyAPI.createTaxonomy({
        name,
        description,
      });
      setTaxonomies((prev) => [...prev, newTaxonomy]);
      return newTaxonomy;
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to create taxonomy";
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  };

  const updateTaxonomy = async (
    id: number,
    name?: string,
    description?: string
  ): Promise<Taxonomy> => {
    try {
      setError(null);
      const updates: any = {};
      if (name !== undefined) updates.name = name;
      if (description !== undefined) updates.description = description;

      const updatedTaxonomy = await TaxonomyAPI.updateTaxonomy(id, updates);
      setTaxonomies((prev) =>
        prev.map((t) => (t.id === id ? updatedTaxonomy : t))
      );
      return updatedTaxonomy;
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to update taxonomy";
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  };

  const deleteTaxonomy = async (id: number): Promise<void> => {
    try {
      setError(null);
      await TaxonomyAPI.deleteTaxonomy(id);
      setTaxonomies((prev) => prev.filter((t) => t.id !== id));
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to delete taxonomy";
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  };

  const createTaxonomyValue = async (
    taxonomyId: number,
    value: string,
    description?: string,
    color?: string
  ): Promise<TaxonomyValue> => {
    try {
      setError(null);
      const newValue = await TaxonomyAPI.createTaxonomyValue(taxonomyId, {
        value,
        description,
        color: color || "#1976d2", // Default blue
      });

      // Update the taxonomy in state to include the new value
      setTaxonomies((prev) =>
        prev.map((t) =>
          t.id === taxonomyId ? { ...t, values: [...t.values, newValue] } : t
        )
      );

      return newValue;
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to create taxonomy value";
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  };

  const updateTaxonomyValue = async (
    valueId: number,
    updates: Partial<TaxonomyValue>
  ): Promise<TaxonomyValue> => {
    try {
      setError(null);
      const updatedValue = await TaxonomyAPI.updateTaxonomyValue(
        valueId,
        updates
      );

      // Update the value in the appropriate taxonomy
      setTaxonomies((prev) =>
        prev.map((t) => ({
          ...t,
          values: t.values.map((v) => (v.id === valueId ? updatedValue : v)),
        }))
      );

      return updatedValue;
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to update taxonomy value";
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  };

  const deleteTaxonomyValue = async (valueId: number): Promise<void> => {
    try {
      setError(null);
      await TaxonomyAPI.deleteTaxonomyValue(valueId);

      // Remove the value from the appropriate taxonomy
      setTaxonomies((prev) =>
        prev.map((t) => ({
          ...t,
          values: t.values.filter((v) => v.id !== valueId),
        }))
      );
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to delete taxonomy value";
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  };

  // Utility functions
  const getTaxonomyById = (id: number): Taxonomy | undefined => {
    return taxonomies.find((t) => t.id === id);
  };

  const getTaxonomyByName = (name: string): Taxonomy | undefined => {
    return taxonomies.find((t) => t.name === name);
  };

  const getValueById = (id: number): TaxonomyValue | undefined => {
    for (const taxonomy of taxonomies) {
      const value = taxonomy.values.find((v) => v.id === id);
      if (value) return value;
    }
    return undefined;
  };

  const getSystemTaxonomies = (): Taxonomy[] => {
    return taxonomies.filter((t) => t.is_system);
  };

  const getUserTaxonomies = (): Taxonomy[] => {
    return taxonomies.filter((t) => !t.is_system);
  };

  // Load initial data
  useEffect(() => {
    refreshTaxonomies();
    refreshPopularTags();
  }, []);

  const value: TaxonomyContextType = {
    // State
    taxonomies,
    popularTags,
    loading,
    error,

    // Actions
    refreshTaxonomies,
    refreshPopularTags,
    createTaxonomy,
    updateTaxonomy,
    deleteTaxonomy,
    createTaxonomyValue,
    updateTaxonomyValue,
    deleteTaxonomyValue,

    // Utility functions
    getTaxonomyById,
    getTaxonomyByName,
    getValueById,
    getSystemTaxonomies,
    getUserTaxonomies,
  };

  return (
    <TaxonomyContext.Provider value={value}>
      {children}
    </TaxonomyContext.Provider>
  );
};

export const useTaxonomy = (): TaxonomyContextType => {
  const context = useContext(TaxonomyContext);
  if (context === undefined) {
    throw new Error("useTaxonomy must be used within a TaxonomyProvider");
  }
  return context;
};
