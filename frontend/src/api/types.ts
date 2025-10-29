// API Response Types

export interface BoundingBox {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
  x_center: number;
  y_center: number;
  width: number;
  height: number;
}

export interface Detection {
  id: number;
  photo_id: number;
  class_name: string;
  confidence: number;
  bbox: BoundingBox;
  created_at: string;
}

export interface Photo {
  id: number;
  filename: string;
  filepath: string;
  timestamp: string;
  width: number;
  height: number;
  session_id: number | null;
  detection_count: number;
  detections: Detection[];
}

export interface Stats {
  total_photos: number;
  total_detections: number;
  unique_classes: number;
  avg_detections_per_photo: number;
  most_detected_class: string | null;
  latest_photo_time: string | null;
  oldest_photo_time: string | null;
  active_session_id: number | null;
}

export interface DetectionSession {
  id: number;
  start_time: string;
  end_time: string | null;
  photo_count: number;
  detection_count: number;
  is_active: boolean;
}

export interface DetectionClass {
  class_name: string;
  count: number;
}

export interface PhotoListResponse {
  photos: Photo[];
  total: number;
  page: number;
  page_size: number;
}

export interface DetectionListResponse {
  detections: Detection[];
  total: number;
  page: number;
  page_size: number;
}
