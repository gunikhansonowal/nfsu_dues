import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: DashboardScreen(),
    );
  }
}

// API 

Future<List<Map<String, String>>> fetchCases() async {
  final response =
      await http.get(Uri.parse('http://localhost:9090/cases'));

  final List data = jsonDecode(response.body);

  return data.map<Map<String, String>>((e) => {
        "caseid": e["caseid"],
        "os": e["os"],
        "originalsize": e["originalsize"],
        "compressedsize": e["compressedsize"],
        "spacesaved": e["spacesaved"],
      }).toList();
}

// DASHBOARD

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int currentPage = 1;
  final int rowsPerPage = 8;

  final TextEditingController searchController = TextEditingController();
  String searchQuery = "";
  String selectedOS = "All";

  List<Map<String, String>> tableData = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    loadData();
  }

  Future<void> loadData() async {
    final data = await fetchCases();
    setState(() {
      tableData = data;
      isLoading = false;
    });
  }

  // FILTERS 

  List<Map<String, String>> get filteredTableData {
    return tableData.where((row) {
      final matchSearch =
          row['caseid']!.toLowerCase().contains(searchQuery.toLowerCase());
      final matchOS = selectedOS == "All" || row['os'] == selectedOS;
      return matchSearch && matchOS;
    }).toList();
  }

  List<Map<String, String>> get paginatedData {
    final start = (currentPage - 1) * rowsPerPage;
    final end = start + rowsPerPage;
    return filteredTableData.sublist(
      start,
      end > filteredTableData.length ? filteredTableData.length : end,
    );
  }

  int get totalPages =>
      (filteredTableData.length / rowsPerPage).ceil().clamp(1, 999);

  double _parseGB(String v) =>
      double.tryParse(v.replaceAll("GB", "").trim()) ?? 0.0;

  double totalOriginal() =>
      filteredTableData.fold(0.0, (s, e) => s + _parseGB(e['originalsize']!));

  double totalCompressed() =>
      filteredTableData.fold(0.0, (s, e) => s + _parseGB(e['compressedsize']!));

  double totalSaved() => totalOriginal() - totalCompressed();

  double averageReduction() {
    if (filteredTableData.isEmpty) return 0;
    double sum = 0;
    for (final e in filteredTableData) {
      final o = _parseGB(e['originalsize']!);
      final c = _parseGB(e['compressedsize']!);
      if (o == 0) continue;
      sum += ((o - c) / o) * 100;
    }
    return sum / filteredTableData.length;
  }

  Color rowColor(int i) =>
      i.isEven ? Colors.green.shade50 : Colors.grey.shade100;

  // PIE CHART  

  List<PieChartSectionData> pieSections() => [
        PieChartSectionData(
          value: totalOriginal(),
          title: "Original",
          color: Colors.green,
          radius: 60,
        ),
        PieChartSectionData(
          value: totalCompressed(),
          title: "Compressed",
          color: Colors.blue,
          radius: 60,
        ),
      ];

  //  EDIT ROW  

  void _editRow(int index) {
    final row = paginatedData[index];
    final realIndex = tableData.indexOf(row);

    final o =
        TextEditingController(text: tableData[realIndex]['originalsize']);
    final c =
        TextEditingController(text: tableData[realIndex]['compressedsize']);

    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text("Edit Case Sizes"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: o,
              decoration:
                  const InputDecoration(labelText: "Original Size (GB)"),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: c,
              decoration:
                  const InputDecoration(labelText: "Compressed Size (GB)"),
            ),
          ],
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("Cancel")),
          ElevatedButton(
            onPressed: () {
              setState(() {
                final orig = _parseGB(o.text);
                final comp = _parseGB(c.text);
                final percent =
                    orig == 0 ? 0 : ((orig - comp) / orig) * 100;

                tableData[realIndex]['originalsize'] = o.text;
                tableData[realIndex]['compressedsize'] = c.text;
                tableData[realIndex]['spacesaved'] =
                    "${percent.toStringAsFixed(1)}%";
              });
              Navigator.pop(context);
            },
            child: const Text("Save"),
          ),
        ],
      ),
    );
  }

  //  UI  

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFFF5F6FA),
      appBar: AppBar(title: const Text("Dashboard")),
      drawer: _sideMenu(context),
      body: Padding(
  padding: const EdgeInsets.all(20),
  child: Row(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      // LEFT SIDE
      Expanded(
        flex: 7,
        child: Column(
          children: [
            _topControls(),
            const SizedBox(height: 12),
            _tableCard(),
          ],
        ),
      ),

      const SizedBox(width: 30),

      // RIGHT SIDE 
      Expanded(
        flex: 3,
        child: Column(
          children: [
            _chartSection(),
            const SizedBox(height: 20),

            // SUMMARY
            _summaryCard(
              "Total Cases",
              filteredTableData.length.toString(),
              Icons.folder,
            ),
            const SizedBox(height: 12),
            _summaryCard(
              "Space Saved",
              "${totalSaved().toStringAsFixed(1)} GB",
              Icons.save,
            ),
          ],
        ),
      ),
    ],
  ),
),

    );
  }

  Widget _topControls() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        SizedBox(
          width: 200,
          child: TextField(
            controller: searchController,
            decoration: const InputDecoration(
              hintText: "Search Case ID",
              prefixIcon: Icon(Icons.search),
              border: OutlineInputBorder(),
              isDense: true,
            ),
            onChanged: (v) {
              setState(() {
                searchQuery = v;
                currentPage = 1;
              });
            },
          ),
        ),
        const SizedBox(width: 12),
        DropdownButton<String>(
          value: selectedOS,
          items: const [
            DropdownMenuItem(value: "All", child: Text("All OS")),
            DropdownMenuItem(value: "Windows", child: Text("Windows")),
            DropdownMenuItem(value: "Linux", child: Text("Linux")),
            DropdownMenuItem(value: "macOS", child: Text("macOS")),
          ],
          onChanged: (v) {
            setState(() {
              selectedOS = v!;
              currentPage = 1;
            });
          },
        ),
      ],
    );
  }

  Widget _summaryCard(String title, String value, IconData icon) {
  return Card(
    elevation: 0,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.zero,
      side: BorderSide(),
    ),
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Icon(icon, color: Colors.indigo),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.normal,
                ),
              ),
              const SizedBox(height: 6),

              Text(
                value,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.normal,
                ),
              ),
            ],
          ),
        ],
      ),
    ),
  );
}


  Widget _tableCard() {
  return Column(
    children: [
      SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: DataTable(
          headingRowColor:
              MaterialStateProperty.all(Colors.indigo.shade100),
          columns: const [
            DataColumn(label: Text("Case ID")),
            DataColumn(label: Text("OS")),
            DataColumn(label: Text("Original Size")),
            DataColumn(label: Text("Compressed Size")),
            DataColumn(label: Text("Space Saved")),
          ],
          rows: List.generate(
            paginatedData.length,
            (i) => DataRow(
              color: MaterialStateProperty.all(rowColor(i)),
              cells: [
                DataCell(Text(paginatedData[i]['caseid']!)),
                DataCell(Text(paginatedData[i]['os']!)),
                DataCell(
                  Text(paginatedData[i]['originalsize']!),
                  onTap: () => _editRow(i),
                ),
                DataCell(
                  Text(paginatedData[i]['compressedsize']!),
                  onTap: () => _editRow(i),
                ),
                DataCell(Text(paginatedData[i]['spacesaved']!)),
              ],
            ),
          ),
        ),
      ),

      const SizedBox(height: 8),

      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          TextButton(
            onPressed:
                currentPage > 1 ? () => setState(() => currentPage--) : null,
            child: const Text("Prev"),
          ),
          Text("Page $currentPage of $totalPages"),
          TextButton(
            onPressed: currentPage < totalPages
                ? () => setState(() => currentPage++)
                : null,
            child: const Text("Next"),
          ),
        ],
      ),
    ],
  );
}


  Widget _chartSection() {
    return Column(
      children: [
        const Text("Overall Size Reduction",
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        SizedBox(
          height: 250,
          child: PieChart(
            PieChartData(sections: pieSections(), centerSpaceRadius: 40),
          ),
        ),
        const SizedBox(height: 12),
        Text(
          "Original: ${totalOriginal().toStringAsFixed(1)} GB\n"
          "Compressed: ${totalCompressed().toStringAsFixed(1)} GB",
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _sideMenu(BuildContext context) {
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          DrawerHeader(
            decoration: const BoxDecoration(color: Colors.indigo),
            child: Row(
              children: const [
                Icon(Icons.dashboard, color: Colors.white, size: 40),
                SizedBox(width: 12),
                Text("My Dashboard",
                    style: TextStyle(color: Colors.white, fontSize: 20)),
              ],
            ),
          ),
          ListTile(
              leading: const Icon(Icons.dashboard),
              title: const Text("Dashboard"),
              onTap: () => Navigator.pop(context)),
          ExpansionTile(
            leading: const Icon(Icons.folder),
            title: const Text("Case Management"),
            children: [
              ListTile(
                  leading: const Icon(Icons.add),
                  title: const Text("Add Case"),
                  onTap: () => Navigator.pop(context)),
              ListTile(
                  leading: const Icon(Icons.list),
                  title: const Text("View Cases"),
                  onTap: () => Navigator.pop(context)),
            ],
          ),
          ListTile(
              leading: const Icon(Icons.download),
              title: const Text("Download File"),
              onTap: () => Navigator.pop(context)),
        ],
      ),
    );
  }
}
