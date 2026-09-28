import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class AnalyticsEngine:
    def __init__(self, data_dir: str = "."):
        self.data_dir = data_dir
        self.df_main = None
        self.df_apartments = None
        self.load_data()

    def load_data(self):
        # Primary cleaned dataset with outlier treatment and missing value imputation
        mvi_path = os.path.join(self.data_dir, "OT_MVI.csv")
        v3_path = os.path.join(self.data_dir, "gurgaon_properties_cleaned_v3.csv")
        apt_path = os.path.join(self.data_dir, "appartments.csv")

        if os.path.exists(mvi_path):
            self.df_main = pd.read_csv(mvi_path)
            if "Unnamed: 0" in self.df_main.columns:
                self.df_main.drop(columns=["Unnamed: 0"], inplace=True)
        elif os.path.exists(v3_path):
            self.df_main = pd.read_csv(v3_path)
        else:
            raise FileNotFoundError("Could not find OT_MVI.csv or gurgaon_properties_cleaned_v3.csv")

        # Clean nulls or unwanted values
        if "built_up_area" in self.df_main.columns:
            self.df_main["built_up_area"] = pd.to_numeric(self.df_main["built_up_area"], errors="coerce")
            self.df_main["built_up_area"] = self.df_main["built_up_area"].fillna(self.df_main["built_up_area"].median())
        
        self.df_main["price"] = pd.to_numeric(self.df_main["price"], errors="coerce")
        self.df_main["price_per_sqft"] = pd.to_numeric(self.df_main["price_per_sqft"], errors="coerce")
        self.df_main["bedRoom"] = pd.to_numeric(self.df_main["bedRoom"], errors="coerce").fillna(2).astype(int)
        self.df_main["bathroom"] = pd.to_numeric(self.df_main["bathroom"], errors="coerce").fillna(2).astype(int)
        self.df_main["balcony"] = self.df_main["balcony"].astype(str).str.strip()
        self.df_main["luxury_score"] = pd.to_numeric(self.df_main["luxury_score"], errors="coerce").fillna(0)
        self.df_main["floorNum"] = pd.to_numeric(self.df_main["floorNum"], errors="coerce").fillna(0)

        # Standardize society and sector
        self.df_main["society"] = self.df_main["society"].astype(str).str.strip().str.title()
        self.df_main["sector"] = self.df_main["sector"].astype(str).str.strip().str.title()
        self.df_main["property_type"] = self.df_main["property_type"].astype(str).str.strip().str.lower()
        self.df_main["facing"] = self.df_main["facing"].astype(str).str.strip().str.title()
        self.df_main["agePossession"] = self.df_main["agePossession"].astype(str).str.strip()

        # Map furnishing types
        furnish_map = {0: "Unfurnished", 1: "Semi-Furnished", 2: "Furnished"}
        if "furnishing_type" in self.df_main.columns:
            self.df_main["furnishing_desc"] = self.df_main["furnishing_type"].map(furnish_map).fillna("Unfurnished")
        else:
            self.df_main["furnishing_desc"] = "Unfurnished"

        # Unique property ID for frontend tracking
        self.df_main["id"] = range(1, len(self.df_main) + 1)

        # Load apartments data if available
        if os.path.exists(apt_path):
            self.df_apartments = pd.read_csv(apt_path)
            self.df_apartments["PropertyName"] = self.df_apartments["PropertyName"].astype(str).str.strip()
        else:
            self.df_apartments = pd.DataFrame()

    def get_overview_kpis(self) -> Dict[str, Any]:
        df = self.df_main
        total_properties = len(df)
        flats_count = int((df["property_type"] == "flat").sum())
        houses_count = int((df["property_type"] == "house").sum())
        
        median_price = round(float(df["price"].median()), 2)
        mean_price = round(float(df["price"].mean()), 2)
        min_price = round(float(df["price"].min()), 2)
        max_price = round(float(df["price"].max()), 2)

        avg_price_sqft = round(float(df["price_per_sqft"].mean()), 0)
        avg_area = round(float(df["built_up_area"].mean()), 0)
        median_area = round(float(df["built_up_area"].median()), 0)
        avg_luxury = round(float(df["luxury_score"].mean()), 1)

        # Top sectors by count
        top_sectors = df["sector"].value_counts().head(8).to_dict()

        # Property type breakdown
        prop_type_data = {
            "labels": ["Flats / Apartments", "Independent Houses"],
            "counts": [flats_count, houses_count],
            "percentages": [round(flats_count / total_properties * 100, 1), round(houses_count / total_properties * 100, 1)]
        }

        # BHK distribution
        bhk_counts = df["bedRoom"].value_counts().sort_index().head(6).to_dict()

        # Furnishing distribution
        furnish_counts = df["furnishing_desc"].value_counts().to_dict()

        # Age / Possession breakdown
        age_counts = df["agePossession"].value_counts().head(6).to_dict()

        return {
            "total_properties": total_properties,
            "flats_count": flats_count,
            "houses_count": houses_count,
            "median_price_cr": median_price,
            "mean_price_cr": mean_price,
            "min_price_cr": min_price,
            "max_price_cr": max_price,
            "avg_price_sqft": avg_price_sqft,
            "avg_area_sqft": avg_area,
            "median_area_sqft": median_area,
            "avg_luxury_score": avg_luxury,
            "top_sectors": top_sectors,
            "property_type_data": prop_type_data,
            "bhk_distribution": bhk_counts,
            "furnishing_distribution": furnish_counts,
            "age_distribution": age_counts
        }

    def get_univariate_analysis(self, feature: str) -> Dict[str, Any]:
        df = self.df_main
        
        numerical_features = ["price", "price_per_sqft", "built_up_area", "bedRoom", "bathroom", "luxury_score", "floorNum"]
        categorical_features = ["property_type", "sector", "facing", "furnishing_desc", "agePossession", "balcony"]

        if feature in numerical_features:
            series = df[feature].dropna()
            
            # Summary Statistics
            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1
            skewness = float(series.skew())
            kurtosis = float(series.kurtosis())
            
            stats = {
                "count": int(series.count()),
                "mean": round(float(series.mean()), 2),
                "std": round(float(series.std()), 2),
                "median": round(float(series.median()), 2),
                "min": round(float(series.min()), 2),
                "q1": round(q1, 2),
                "q3": round(q3, 2),
                "max": round(float(series.max()), 2),
                "iqr": round(iqr, 2),
                "skewness": round(skewness, 3),
                "kurtosis": round(kurtosis, 3),
                "is_numerical": True
            }

            # Histogram & Distribution Bins
            num_bins = 25 if feature in ["price", "price_per_sqft", "built_up_area", "luxury_score"] else min(15, len(series.unique()))
            counts, bin_edges = np.histogram(series, bins=num_bins)
            
            bin_labels = [f"{round(bin_edges[i], 1)} - {round(bin_edges[i+1], 1)}" for i in range(len(counts))]
            bin_midpoints = [round((bin_edges[i] + bin_edges[i+1]) / 2, 2) for i in range(len(counts))]

            # Boxplot data points
            box_data = {
                "min": round(float(series.min()), 2),
                "q1": round(q1, 2),
                "median": round(float(series.median()), 2),
                "q3": round(q3, 2),
                "max": round(float(series.max()), 2),
                "outlier_low": round(max(float(series.min()), q1 - 1.5 * iqr), 2),
                "outlier_high": round(min(float(series.max()), q3 + 1.5 * iqr), 2)
            }

            # Flat vs House comparison
            flat_series = df[df["property_type"] == "flat"][feature].dropna()
            house_series = df[df["property_type"] == "house"][feature].dropna()
            comparison = {
                "flat": {
                    "mean": round(float(flat_series.mean()), 2) if len(flat_series) else 0,
                    "median": round(float(flat_series.median()), 2) if len(flat_series) else 0,
                    "std": round(float(flat_series.std()), 2) if len(flat_series) else 0
                },
                "house": {
                    "mean": round(float(house_series.mean()), 2) if len(house_series) else 0,
                    "median": round(float(house_series.median()), 2) if len(house_series) else 0,
                    "std": round(float(house_series.std()), 2) if len(house_series) else 0
                }
            }

            return {
                "feature": feature,
                "is_numerical": True,
                "stats": stats,
                "histogram": {
                    "labels": bin_labels,
                    "midpoints": bin_midpoints,
                    "counts": counts.tolist()
                },
                "box_data": box_data,
                "comparison": comparison
            }

        elif feature in categorical_features:
            series = df[feature].dropna()
            if feature == "sector":
                val_counts = series.value_counts().head(20)
            else:
                val_counts = series.value_counts()

            return {
                "feature": feature,
                "is_numerical": False,
                "categories": {
                    "labels": val_counts.index.tolist(),
                    "counts": val_counts.values.tolist(),
                    "percentages": [round(c / len(df) * 100, 1) for c in val_counts.values]
                },
                "unique_count": int(series.nunique())
            }
        else:
            return {"error": f"Unknown feature '{feature}'"}

    def get_multivariate_analysis(self) -> Dict[str, Any]:
        df = self.df_main
        
        # Features for correlation matrix
        num_cols = ["price", "price_per_sqft", "built_up_area", "bedRoom", "bathroom", "floorNum", "luxury_score"]
        room_cols = ["study room", "servant room", "store room", "pooja room"]
        for rc in room_cols:
            if rc in df.columns:
                num_cols.append(rc)

        corr_df = df[num_cols].corr()
        corr_matrix = {
            "columns": num_cols,
            "data": [[round(float(val), 3) for val in row] for row in corr_df.values]
        }

        # Sample scatter points for Area vs Price & Luxury Score vs Price (capped for fast render)
        sample_df = df.sample(n=min(600, len(df)), random_state=42)
        scatter_area_price = [
            {
                "x": round(float(row["built_up_area"]), 1),
                "y": round(float(row["price"]), 2),
                "type": row["property_type"],
                "bhk": int(row["bedRoom"]),
                "sector": row["sector"],
                "society": row["society"]
            }
            for _, row in sample_df.iterrows()
            if pd.notnull(row["built_up_area"]) and pd.notnull(row["price"])
        ]

        scatter_luxury_price = [
            {
                "x": round(float(row["luxury_score"]), 1),
                "y": round(float(row["price"]), 2),
                "type": row["property_type"],
                "bhk": int(row["bedRoom"]),
                "sector": row["sector"]
            }
            for _, row in sample_df.iterrows()
            if pd.notnull(row["luxury_score"]) and pd.notnull(row["price"])
        ]

        # Price by BHK aggregation
        bhk_price = df.groupby("bedRoom")["price"].agg(["median", "mean", "count"]).reset_index()
        bhk_price = bhk_price[bhk_price["count"] >= 5].sort_values("bedRoom")
        
        # Price by Furnishing
        furnish_price = df.groupby("furnishing_desc")["price"].agg(["median", "mean", "count"]).reset_index()

        # Property type vs Price & Price/SqFt
        type_agg = df.groupby("property_type").agg({
            "price": ["median", "mean"],
            "price_per_sqft": ["median", "mean"],
            "built_up_area": ["median", "mean"],
            "luxury_score": ["mean"]
        }).round(2)
        
        # Flatten tuple columns to string keys
        type_comparison = {}
        for ptype in type_agg.index:
            type_comparison[ptype] = {
                f"{col[0]}_{col[1]}": float(type_agg.loc[ptype, col])
                for col in type_agg.columns
            }

        return {
            "correlation_matrix": corr_matrix,
            "scatter_area_price": scatter_area_price,
            "scatter_luxury_price": scatter_luxury_price,
            "bhk_price": {
                "bhk": [int(x) for x in bhk_price["bedRoom"].tolist()],
                "median_price": [round(float(v), 2) for v in bhk_price["median"]],
                "mean_price": [round(float(v), 2) for v in bhk_price["mean"]],
                "count": [int(x) for x in bhk_price["count"].tolist()]
            },
            "furnish_price": {
                "labels": [str(x) for x in furnish_price["furnishing_desc"].tolist()],
                "median_price": [round(float(v), 2) for v in furnish_price["median"]],
                "mean_price": [round(float(v), 2) for v in furnish_price["mean"]]
            },
            "type_comparison": type_comparison
        }

    def get_sectors_intelligence(self) -> Dict[str, Any]:
        df = self.df_main
        
        # Sector aggregations (minimum 5 properties for reliable stats)
        sector_agg = df.groupby("sector").agg(
            total_properties=("price", "count"),
            median_price=("price", "median"),
            avg_price=("price", "mean"),
            avg_price_sqft=("price_per_sqft", "mean"),
            avg_area=("built_up_area", "mean"),
            avg_luxury=("luxury_score", "mean")
        ).reset_index()

        # Filter significant sectors
        sector_agg_sig = sector_agg[sector_agg["total_properties"] >= 5].copy()

        # Top 10 Most Expensive Sectors
        top_expensive = sector_agg_sig.sort_values("avg_price", ascending=False).head(10).to_dict(orient="records")
        for item in top_expensive:
            for k in ["median_price", "avg_price", "avg_price_sqft", "avg_area", "avg_luxury"]:
                item[k] = round(float(item[k]), 1)

        # Top 10 Most Affordable Sectors
        top_affordable = sector_agg_sig.sort_values("avg_price", ascending=True).head(10).to_dict(orient="records")
        for item in top_affordable:
            for k in ["median_price", "avg_price", "avg_price_sqft", "avg_area", "avg_luxury"]:
                item[k] = round(float(item[k]), 1)

        # Top 10 Highest Volume Sectors
        top_volume = sector_agg.sort_values("total_properties", ascending=False).head(10).to_dict(orient="records")
        for item in top_volume:
            for k in ["median_price", "avg_price", "avg_price_sqft", "avg_area", "avg_luxury"]:
                item[k] = round(float(item[k]), 1)

        # All sector names sorted
        all_sectors = sorted(df["sector"].unique().tolist())

        return {
            "all_sectors": all_sectors,
            "top_expensive": top_expensive,
            "top_affordable": top_affordable,
            "top_volume": top_volume
        }

    def get_sector_deep_dive(self, sector_name: str) -> Dict[str, Any]:
        df = self.df_main
        sec_df = df[df["sector"].str.lower() == sector_name.strip().lower()]

        if sec_df.empty:
            return {"error": f"Sector '{sector_name}' not found."}

        total = len(sec_df)
        flats = int((sec_df["property_type"] == "flat").sum())
        houses = int((sec_df["property_type"] == "house").sum())
        
        top_societies = sec_df["society"].value_counts().head(8).to_dict()
        bhk_dist = sec_df["bedRoom"].value_counts().sort_index().to_dict()

        return {
            "sector": sector_name,
            "total_properties": total,
            "flats": flats,
            "houses": houses,
            "median_price": round(float(sec_df["price"].median()), 2),
            "mean_price": round(float(sec_df["price"].mean()), 2),
            "min_price": round(float(sec_df["price"].min()), 2),
            "max_price": round(float(sec_df["price"].max()), 2),
            "avg_price_sqft": round(float(sec_df["price_per_sqft"].mean()), 0),
            "avg_area": round(float(sec_df["built_up_area"].mean()), 0),
            "avg_luxury": round(float(sec_df["luxury_score"].mean()), 1),
            "top_societies": top_societies,
            "bhk_distribution": bhk_dist,
            "properties_sample": sec_df[["id", "property_type", "society", "price", "built_up_area", "bedRoom", "bathroom", "luxury_score", "furnishing_desc"]].head(15).to_dict(orient="records")
        }

    def filter_properties(
        self,
        property_type: Optional[str] = None,
        sector: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_area: Optional[float] = None,
        max_area: Optional[float] = None,
        bedrooms: Optional[List[int]] = None,
        furnishing: Optional[str] = None,
        min_luxury: Optional[float] = None,
        study_room: Optional[bool] = None,
        servant_room: Optional[bool] = None,
        store_room: Optional[bool] = None,
        pooja_room: Optional[bool] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "price",
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        df = self.df_main.copy()

        # Filters
        if property_type and property_type.lower() != "all":
            df = df[df["property_type"] == property_type.lower()]

        if sector and sector.lower() != "all":
            df = df[df["sector"].str.lower() == sector.lower()]

        if min_price is not None:
            df = df[df["price"] >= min_price]

        if max_price is not None:
            df = df[df["price"] <= max_price]

        if min_area is not None:
            df = df[df["built_up_area"] >= min_area]

        if max_area is not None:
            df = df[df["built_up_area"] <= max_area]

        if bedrooms and len(bedrooms) > 0:
            df = df[df["bedRoom"].isin(bedrooms)]

        if furnishing and furnishing.lower() != "all":
            df = df[df["furnishing_desc"].str.lower() == furnishing.lower()]

        if min_luxury is not None and min_luxury > 0:
            df = df[df["luxury_score"] >= min_luxury]

        if study_room and "study room" in df.columns:
            df = df[df["study room"] == 1]

        if servant_room and "servant room" in df.columns:
            df = df[df["servant room"] == 1]

        if store_room and "store room" in df.columns:
            df = df[df["store room"] == 1]

        if pooja_room and "pooja room" in df.columns:
            df = df[df["pooja room"] == 1]

        if search_query:
            q = search_query.strip().lower()
            df = df[
                df["society"].str.lower().str.contains(q, na=False) |
                df["sector"].str.lower().str.contains(q, na=False) |
                df["description"].str.lower().str.contains(q, na=False)
            ]

        total_matching = len(df)

        # Sorting
        if sort_by in df.columns:
            ascending = (sort_order.lower() == "asc")
            df = df.sort_values(sort_by, ascending=ascending)

        # Pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_df = df.iloc[start_idx:end_idx]

        cols_to_return = [
            "id", "property_type", "society", "sector", "price", "price_per_sqft",
            "built_up_area", "bedRoom", "bathroom", "balcony", "floorNum",
            "facing", "agePossession", "furnishing_desc", "luxury_score"
        ]
        available_cols = [c for c in cols_to_return if c in paginated_df.columns]

        records = paginated_df[available_cols].to_dict(orient="records")

        return {
            "total_count": total_matching,
            "page": page,
            "page_size": page_size,
            "total_pages": int(np.ceil(total_matching / page_size)) if total_matching > 0 else 1,
            "records": records
        }

    def get_property_by_id(self, prop_id: int) -> Optional[Dict[str, Any]]:
        df = self.df_main
        match = df[df["id"] == prop_id]
        if match.empty:
            return None
        return match.iloc[0].to_dict()
