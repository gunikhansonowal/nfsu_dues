package main

import (
	"encoding/json"
	"net/http"
)

type Case struct {
	CaseID         string `json:"caseid"`
	OS             string `json:"os"`
	OriginalSize   string `json:"originalsize"`
	CompressedSize string `json:"compressedsize"`
	SpaceSaved     string `json:"spacesaved"`
}

func casesHandler(w http.ResponseWriter, r *http.Request) {

	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}

	w.Header().Set("Content-Type", "application/json")

	data := []Case{
		{"01", "Windows", "4GB", "1GB", "25%"},
		{"02", "Linux", "7GB", "2GB", "28.57%"},
		{"03", "macOS", "65GB", "20GB", "30.77%"},
		{"04", "Windows", "20GB", "6GB", "30%"},
		{"05", "Linux", "38GB", "10GB", "26.31%"},
		{"06", "Windows", "40GB", "12GB", "30%"},
		{"07", "macOS", "15GB", "4GB", "26.67%"},
		{"08", "Linux", "70GB", "30GB", "42.86%"},
		{"09", "Windows", "10GB", "4GB", "40%"},
		{"10", "macOS", "65GB", "20GB", "30.77%"},
		{"11", "Windows", "4GB", "1GB", "25%"},
		{"12", "Linux", "7GB", "2GB", "28.57%"},
		{"13", "macOS", "65GB", "20GB", "30.77%"},
		{"14", "Windows", "20GB", "6GB", "30%"},
		{"15", "Linux", "38GB", "10GB", "26.31%"},
		{"16", "Windows", "40GB", "12GB", "30%"},
		{"17", "macOS", "15GB", "4GB", "26.67%"},
		{"18", "Linux", "70GB", "30GB", "42.86%"},
		{"19", "Windows", "10GB", "4GB", "40%"},
		{"20", "macOS", "65GB", "20GB", "30.77%"},
	}

	json.NewEncoder(w).Encode(data)
}

func main() {
	http.HandleFunc("/cases", casesHandler)

	println("Go server running on http://localhost:9090")

	err := http.ListenAndServe(":9090", nil)
	if err != nil {
		panic(err)
	}
}
