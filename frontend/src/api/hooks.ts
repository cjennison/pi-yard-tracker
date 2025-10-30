import { useQuery } from "@tanstack/react-query";
import type { UseQueryOptions } from "@tanstack/react-query";
import apiClient from "./client";
import type {
  Stats,
  Photo,
  DetectionClass,
  DetectionSession,
  Detection,
} from "./types";

// Stats API
export const useStats = (options?: UseQueryOptions<Stats>) => {
  return useQuery<Stats>({
    queryKey: ["stats"],
    queryFn: async () => {
      const { data } = await apiClient.get<Stats>("/stats");
      return data;
    },
    refetchInterval: 5000, // Auto-refresh every 5 seconds
    ...options,
  });
};

// Photos API - Updated to match backend response format
export const usePhotos = (
  params?: {
    page?: number;
    limit?: number;
    has_detections?: boolean;
    min_detections?: number;
  },
  options?: UseQueryOptions<{
    photos: Photo[];
    total: number;
    page: number;
    page_size: number;
  }>
) => {
  return useQuery<{
    photos: Photo[];
    total: number;
    page: number;
    page_size: number;
  }>({
    queryKey: ["photos", params],
    queryFn: async () => {
      const offset = params?.page
        ? (params.page - 1) * (params.limit || 20)
        : 0;
      const { data } = await apiClient.get<Photo[]>("/photos/", {
        params: {
          offset,
          limit: params?.limit || 20,
          has_detections: params?.has_detections,
          min_detections: params?.min_detections,
        },
      });

      // Transform the response to match expected format
      return {
        photos: data,
        total: data.length, // Backend doesn't return total, so we use array length
        page: params?.page || 1,
        page_size: params?.limit || 20,
      };
    },
    ...options,
  });
};

// Single Photo API
export const usePhoto = (
  photoId: number | null,
  options?: UseQueryOptions<Photo>
) => {
  return useQuery<Photo>({
    queryKey: ["photo", photoId],
    queryFn: async () => {
      if (!photoId) throw new Error("Photo ID is required");
      const { data } = await apiClient.get<Photo>(`/photos/${photoId}`);
      return data;
    },
    enabled: !!photoId,
    ...options,
  });
};

// Detections API - Updated to match backend response format
export const useDetections = (
  params?: {
    page?: number;
    limit?: number;
    class_name?: string;
    min_confidence?: number;
    max_confidence?: number;
  },
  options?: UseQueryOptions<{
    detections: Detection[];
    total: number;
    page: number;
    page_size: number;
  }>
) => {
  return useQuery<{
    detections: Detection[];
    total: number;
    page: number;
    page_size: number;
  }>({
    queryKey: ["detections", params],
    queryFn: async () => {
      const offset = params?.page
        ? (params.page - 1) * (params.limit || 20)
        : 0;
      const { data } = await apiClient.get<Detection[]>("/detections/", {
        params: {
          offset,
          limit: params?.limit || 20,
          class_name: params?.class_name,
          min_confidence: params?.min_confidence,
          max_confidence: params?.max_confidence,
        },
      });

      // Transform the response to match expected format
      return {
        detections: data,
        total: data.length, // Backend doesn't return total, so we use array length
        page: params?.page || 1,
        page_size: params?.limit || 20,
      };
    },
    ...options,
  });
};

// Detection Classes API
export const useDetectionClasses = (
  options?: UseQueryOptions<DetectionClass[]>
) => {
  return useQuery<DetectionClass[]>({
    queryKey: ["detection-classes"],
    queryFn: async () => {
      const { data } = await apiClient.get<DetectionClass[]>(
        "/detections/classes"
      );
      return data;
    },
    refetchInterval: 10000, // Auto-refresh every 10 seconds
    ...options,
  });
};

// Sessions API
export const useSessions = (
  params?: {
    page?: number;
    limit?: number;
    active_only?: boolean;
  },
  options?: UseQueryOptions<DetectionSession[]>
) => {
  return useQuery<DetectionSession[]>({
    queryKey: ["sessions", params],
    queryFn: async () => {
      const { data } = await apiClient.get<DetectionSession[]>("/sessions", {
        params: {
          offset: params?.page ? (params.page - 1) * (params.limit || 20) : 0,
          limit: params?.limit || 20,
          active_only: params?.active_only,
        },
      });
      return data;
    },
    ...options,
  });
};
