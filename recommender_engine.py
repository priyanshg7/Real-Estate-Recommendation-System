import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics.pairwise import cosine_similarity

class RecommenderEngine:
    def __init__(self, analytics_engine):
        self.analytics = analytics_engine
        self.df = analytics_engine.df_main.copy()
        self.model = None
        self.preprocessor = None
        self.feature_matrix = None
        self.scaled_matrix = None
        self._init_models()

    def _init_models(self):
        # Prepare training data for price estimation
        train_df = self.df.dropna(subset=["price", "built_up_area", "sector", "bedRoom", "bathroom"]).copy()
        
        categorical_features = ["property_type", "sector", "furnishing_desc"]
        numeric_features = ["built_up_area", "bedRoom", "bathroom", "floorNum", "luxury_score"]
        
        # Include room features if available
        room_cols = ["study room", "servant room", "store room", "pooja room"]
        for r in room_cols:
            if r in train_df.columns:
                numeric_features.append(r)

        self.preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), numeric_features),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features)
            ]
        )

        self.model = Pipeline([
            ("preprocessor", self.preprocessor),
            ("regressor", RandomForestRegressor(n_estimators=100, max_depth=16, random_state=42, n_jobs=-1))
        ])

        X = train_df[categorical_features + numeric_features]
        y = train_df["price"]
        self.model.fit(X, y)

        # Build Recommendation Matrix (Normalized numeric vectors for similarity)
        rec_numeric = ["price", "built_up_area", "bedRoom", "bathroom", "luxury_score"]
        for r in room_cols:
            if r in self.df.columns:
                rec_numeric.append(r)

        rec_features = self.df[rec_numeric].fillna(0).values
        scaler = StandardScaler()
        self.scaled_matrix = scaler.fit_transform(rec_features)
        self.rec_scaler = scaler
        self.rec_numeric_cols = rec_numeric

    def predict_price(
        self,
        property_type: str,
        sector: str,
        built_up_area: float,
        bedRoom: int,
        bathroom: int,
        floorNum: float = 2.0,
        luxury_score: float = 30.0,
        furnishing_desc: str = "Semi-Furnished",
        study_room: int = 0,
        servant_room: int = 0,
        store_room: int = 0,
        pooja_room: int = 0
    ) -> Dict[str, Any]:
        # Clean inputs
        property_type = property_type.lower().strip()
        sector = sector.title().strip()
        furnishing_desc = furnishing_desc.strip()

        input_data = {
            "property_type": [property_type],
            "sector": [sector],
            "furnishing_desc": [furnishing_desc],
            "built_up_area": [float(built_up_area)],
            "bedRoom": [int(bedRoom)],
            "bathroom": [int(bathroom)],
            "floorNum": [float(floorNum)],
            "luxury_score": [float(luxury_score)],
            "study room": [int(study_room)],
            "servant room": [int(servant_room)],
            "store room": [int(store_room)],
            "pooja room": [int(pooja_room)]
        }

        input_df = pd.DataFrame(input_data)
        predicted_price = float(self.model.predict(input_df)[0])
        predicted_price = max(0.1, round(predicted_price, 2))

        # Price per sq ft estimation
        price_per_sqft = round((predicted_price * 10000000) / built_up_area, 0) if built_up_area > 0 else 0

        # Market confidence range (+- 10%)
        price_low = round(predicted_price * 0.90, 2)
        price_high = round(predicted_price * 1.10, 2)

        # Sector benchmark comparison
        sec_df = self.df[self.df["sector"].str.lower() == sector.lower()]
        sector_avg_price = round(float(sec_df["price"].mean()), 2) if not sec_df.empty else predicted_price
        sector_avg_sqft = round(float(sec_df["price_per_sqft"].mean()), 0) if not sec_df.empty else price_per_sqft

        return {
            "estimated_price_cr": predicted_price,
            "estimated_range": f"INR {price_low} Cr - {price_high} Cr",
            "price_per_sqft": price_per_sqft,
            "sector_benchmark": {
                "sector": sector,
                "sector_avg_price_cr": sector_avg_price,
                "sector_avg_sqft": sector_avg_sqft,
                "comparison_pct": round(((predicted_price - sector_avg_price) / sector_avg_price) * 100, 1) if sector_avg_price > 0 else 0
            }
        }

    def recommend_properties(
        self,
        budget_min: float,
        budget_max: float,
        target_sector: Optional[str] = None,
        property_type: Optional[str] = "all",
        preferred_bhk: Optional[int] = None,
        min_luxury: float = 0.0,
        need_servant_room: bool = False,
        need_study_room: bool = False,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        df = self.df.copy()

        # Hard constraints with slight tolerance
        budget_buffer_min = max(0.0, budget_min * 0.85)
        budget_buffer_max = budget_max * 1.20

        mask = (df["price"] >= budget_buffer_min) & (df["price"] <= budget_buffer_max)
        if property_type and property_type.lower() != "all":
            mask &= (df["property_type"] == property_type.lower())

        candidates = df[mask].copy()

        if candidates.empty:
            # Fallback to nearest budget candidates
            candidates = df.sort_values(by="price").head(30).copy()

        # Score candidates based on multi-factor preference matching
        scores = []
        target_budget = (budget_min + budget_max) / 2.0

        for idx, row in candidates.iterrows():
            score = 100.0

            # 1. Budget proximity (up to 30 pts)
            price_diff_ratio = abs(row["price"] - target_budget) / target_budget
            budget_penalty = min(30.0, price_diff_ratio * 30.0)
            score -= budget_penalty

            # 2. Sector matching (up to 25 pts)
            if target_sector and target_sector.lower() != "all":
                if row["sector"].strip().lower() == target_sector.strip().lower():
                    score += 15.0
                else:
                    score -= 15.0

            # 3. BHK matching (up to 20 pts)
            if preferred_bhk is not None and preferred_bhk > 0:
                bhk_diff = abs(row["bedRoom"] - preferred_bhk)
                if bhk_diff == 0:
                    score += 10.0
                elif bhk_diff == 1:
                    score -= 5.0
                else:
                    score -= 15.0

            # 4. Luxury score bonus (up to 15 pts)
            if row["luxury_score"] >= min_luxury:
                score += min(15.0, (row["luxury_score"] / 100.0) * 15.0)
            else:
                score -= 10.0

            # 5. Room preferences
            if need_servant_room and row.get("servant room", 0) == 1:
                score += 5.0
            if need_study_room and row.get("study room", 0) == 1:
                score += 5.0

            # Normalize to 0-100
            final_match = max(40.0, min(99.0, round(score, 1)))
            scores.append(final_match)

        candidates["match_score"] = scores
        ranked = candidates.sort_values(by=["match_score", "luxury_score"], ascending=[False, False]).head(top_k)

        results = []
        for _, row in ranked.iterrows():
            # Build match highlights
            highlights = []
            if abs(row["price"] - target_budget) <= (target_budget * 0.15):
                highlights.append("🎯 Fits Target Budget")
            if target_sector and row["sector"].strip().lower() == target_sector.strip().lower():
                highlights.append(f"📍 Prime Location in {row['sector']}")
            if preferred_bhk and row["bedRoom"] == preferred_bhk:
                highlights.append(f"🛏️ Exact {int(row['bedRoom'])} BHK match")
            if row["luxury_score"] >= 40:
                highlights.append(f"⭐ High Luxury Index ({int(row['luxury_score'])})")
            if row.get("servant room", 0) == 1:
                highlights.append("🧑‍🍳 Servant Room Included")
            if row.get("study room", 0) == 1:
                highlights.append("📚 Study Room Included")

            results.append({
                "id": int(row["id"]),
                "property_type": row["property_type"].capitalize(),
                "society": row["society"],
                "sector": row["sector"],
                "price": round(float(row["price"]), 2),
                "price_per_sqft": round(float(row["price_per_sqft"]), 0),
                "built_up_area": round(float(row["built_up_area"]), 0),
                "bedRoom": int(row["bedRoom"]),
                "bathroom": int(row["bathroom"]),
                "luxury_score": int(row["luxury_score"]),
                "furnishing_desc": row["furnishing_desc"],
                "match_score": float(row["match_score"]),
                "highlights": highlights
            })

        return results
