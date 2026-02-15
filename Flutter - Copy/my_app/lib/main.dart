import 'package:flutter/material.dart';
import 'dart:async';

void main() {
  runApp(const ForensicApp());
}

/* ================= MAIN APP ================= */

class ForensicApp extends StatelessWidget {
  const ForensicApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Forensic Deduplication Tool',
      theme: ThemeData(primarySwatch: Colors.indigo),
      home: const DashboardPage(),
    );
  }
}

/* ================= DASHBOARD ================= */

class DashboardPage extends StatelessWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Forensic Dashboard")),
      drawer: Drawer(
        child: ListView(
          children: [
            const DrawerHeader(
              decoration: BoxDecoration(color: Colors.indigo),
              child: Text(
                "Forensic Tool Menu",
                style: TextStyle(color: Colors.white, fontSize: 22),
              ),
            ),
            ListTile(
              leading: const Icon(Icons.folder),
              title: const Text("Case Management"),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const CaseManagementPage()),
                );
              },
            ),
          ],
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(12.0),
        child: ListView.builder(
          itemCount: 10,
          itemBuilder: (context, index) {
            return Card(
              elevation: 3,
              margin: const EdgeInsets.symmetric(vertical: 8),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
              child: ListTile(
                leading: const Icon(Icons.description, size: 32),
                title: Text(
                  "Case ID: 10${index + 1}",
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                subtitle: const Text("Investigator: Admin"),
              ),
            );
          },
        ),
      ),
    );
  }
}

/* ================= CASE MANAGEMENT ================= */

class CaseManagementPage extends StatelessWidget {
  const CaseManagementPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Case Management")),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 220,
              child: ElevatedButton.icon(
                icon: const Icon(Icons.add),
                label: const Text("New Case"),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const NewCasePage()),
                  );
                },
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: 220,
              child: ElevatedButton.icon(
                icon: const Icon(Icons.folder_open),
                label: const Text("Open Existing Case"),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const OpenCasePage()),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/* ================= NEW CASE ================= */

class NewCasePage extends StatefulWidget {
  const NewCasePage({super.key});

  @override
  State<NewCasePage> createState() => _NewCasePageState();
}

class _NewCasePageState extends State<NewCasePage> {
  final TextEditingController _dateController = TextEditingController();
  String? _selectedOS;
  final List<String> _osOptions = [
    'Windows',
    'Linux',
    'Android',
    'iOS',
    'Other',
  ];

  @override
  void dispose() {
    _dateController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("New Case")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            _buildTextField("Case ID"),
            const SizedBox(height: 15),
            _buildTextField("Investigator Name"),
            const SizedBox(height: 15),
            _buildTextField("Brief Description", maxLines: 3),
            const SizedBox(height: 15),
            _buildDateField(),
            const SizedBox(height: 40),

            // Upload + OS in Row
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Upload Button
                SizedBox(
                  width: 150,
                  height: 48,
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.upload),
                    label: const Text("Upload"),
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const ProcessingPage(),
                        ),
                      );
                    },
                  ),
                ),
                const SizedBox(width: 15),
                // OS Selector as button
                SizedBox(
                  width: 150,
                  height: 48,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.indigo,
                      padding: EdgeInsets.zero,
                    ),
                    onPressed: () {},
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<String>(
                        value: _selectedOS,
                        dropdownColor: Colors.white,
                        iconEnabledColor: Colors.white,
                        hint: const Text(
                          "Select OS",
                          style: TextStyle(color: Colors.white),
                        ),
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                        ),
                        items: _osOptions.map((os) {
                          return DropdownMenuItem(value: os, child: Text(os));
                        }).toList(),
                        onChanged: (value) {
                          setState(() {
                            _selectedOS = value;
                          });
                        },
                      ),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 25),

            // Submit Case Button
            Center(
              child: SizedBox(
                width: 220,
                height: 48,
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.check_circle),
                  label: const Text("Submit Case"),
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text("Case submitted successfully"),
                      ),
                    );
                    Navigator.pop(context);
                  },
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTextField(String label, {int maxLines = 1}) {
    return TextField(
      maxLines: maxLines,
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
      ),
    );
  }

  Widget _buildDateField() {
    return TextField(
      controller: _dateController,
      readOnly: true,
      decoration: InputDecoration(
        labelText: "Date",
        hintText: "DD/MM/YYYY",
        border: const OutlineInputBorder(),
        suffixIcon: const Icon(Icons.calendar_today),
      ),
      onTap: () async {
        DateTime? pickedDate = await showDatePicker(
          context: context,
          initialDate: DateTime.now(),
          firstDate: DateTime(2000),
          lastDate: DateTime(2100),
        );
        if (pickedDate != null) {
          String formattedDate =
              "${pickedDate.day.toString().padLeft(2, '0')}/${pickedDate.month.toString().padLeft(2, '0')}/${pickedDate.year}";
          setState(() {
            _dateController.text = formattedDate;
          });
        }
      },
    );
  }
}

/* ================= OPEN CASE ================= */

class OpenCasePage extends StatelessWidget {
  const OpenCasePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Open Existing Cases")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView.builder(
          itemCount: 10,
          itemBuilder: (context, index) {
            String caseId = "FD-2026-00$index";
            return Card(
              elevation: 3,
              margin: const EdgeInsets.only(bottom: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
              child: ListTile(
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 10,
                ),
                leading: const Icon(Icons.folder, size: 32),
                title: Text(
                  'Case ID: $caseId',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                subtitle: const Padding(
                  padding: EdgeInsets.only(top: 6),
                  child: Text(
                    'Investigator: John Doe\nDigital evidence analysis',
                  ),
                ),
                isThreeLine: true,
                trailing: ElevatedButton(
                  child: const Text("Upload"),
                  onPressed: () {
                    _showUploadDialog(context, caseId);
                  },
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  void _showUploadDialog(BuildContext context, String caseId) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Upload Evidence for $caseId'),
        content: const Text('Do you want to upload new evidence to this case?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Evidence Uploaded for $caseId')),
              );
            },
            child: const Text('Yes'),
          ),
        ],
      ),
    );
  }
}

/* ================= PROCESSING ================= */

class ProcessingPage extends StatefulWidget {
  const ProcessingPage({super.key});

  @override
  State<ProcessingPage> createState() => _ProcessingPageState();
}

class _ProcessingPageState extends State<ProcessingPage> {
  double progress = 0.0;

  @override
  void initState() {
    super.initState();
    startProcessing();
  }

  void startProcessing() {
    Timer.periodic(const Duration(milliseconds: 500), (timer) {
      setState(() {
        progress += 0.1;
        if (progress >= 1.0) timer.cancel();
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Processing Evidence")),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text(
                "Removing Duplicate Files",
                style: TextStyle(fontSize: 18),
              ),
              const SizedBox(height: 20),
              LinearProgressIndicator(value: progress),
              const SizedBox(height: 10),
              Text("${(progress * 100).toInt()} % Completed"),
              const SizedBox(height: 20),
              const Text(
                "Deduplication using hash comparison (SHA-256)",
                style: TextStyle(fontSize: 12, color: Colors.grey),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
